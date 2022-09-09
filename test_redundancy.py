import aciClient
import logging
import os
import re

logging.basicConfig(level=logging.INFO)

IS_MULTIPOD = False
fontcolors = {"OK": "\033[92m", "FAIL": "\033[91m", "INFO": "\033[93m"}

aci = aciClient.ACI(
    os.environ["ACI_HOST"], os.environ["ACI_USER"], os.environ["ACI_PASS"]
)

nodes = {
    "controller": [],
    "spine": [],
    "leaf": [],
}
dn2hostname = {}


def print_title(title):
    print(f"{fontcolors['INFO']}" + "=" * 90)
    print(f"{fontcolors['INFO']} {title}")
    print(f"{fontcolors['INFO']}" + "=" * 90)


def print_msg(msg, ok=True):
    if ok:
        print(f"{fontcolors['OK']}OK: {msg}")
    else:
        print(f"{fontcolors['FAIL']}ERROR: {msg}")


def check_neighbor_redundancy(molist, check_field, regex=False):
    redundancy = set()
    key = list(molist[0].keys())[0]
    for mo in molist:
        if regex:
            redundancy.add(
                re.match(regex[0], mo[key]["attributes"][check_field]).group(regex[1])
            )
        else:
            redundancy.add(mo[key]["attributes"][check_field])
    return len(redundancy) > 1


def check_status(moclass):
    # and({settings[moclass]["filter1"][0]}({moclass}.{settings[moclass]["filter1"][1]},"{settings[moclass]["filter1"][2]}"),{settings[moclass]["filter2"][0]}({moclass}.{settings[moclass]["filter2"][1]},"{settings[moclass]["filter2"][2]}"))
    settings = {
        "lldpAdjEp": {
            "title": "checking apic uplinks",
            "nodetype": "controller",
            "filter": ('wcard(lldpAdjEp.dn,"eth2/")'),
            "ok_cnt": 2,
            "check_field": "sysDesc",
            "re": False,
            "msg_suffix": "fabric uplinks",
        },
        "ospfAdjEp": {
            "title": "checking multipod uplinks",
            "nodetype": "spine",
            "filter": 'and(wcard(ospfAdjEp.dn,"dom-overlay-1"),eq(ospfAdjEp.operSt,"full"))',
            "ok_cnt": 1,
            "check_field": "dn",
            "re": (r".*/(adj-\d+.\d+.\d+.\d+)", 1),
            "msg_suffix": "IPN neighbors",
        },
        "isisAdjEp": {
            "title": "checking leaf uplinks",
            "nodetype": "leaf",
            "filter": 'and(wcard(isisAdjEp.dn,"dom-overlay-1"),eq(isisAdjEp.operSt,"up"))',
            "ok_cnt": 2,
            "check_field": "name",
            "re": False,
            "msg_suffix": "ISIS neighbors",
        },
    }

    print_title(settings[moclass]["title"])

    check_control = {}
    for node in nodes[settings[moclass]["nodetype"]]:
        check_control[node] = {
            "cnt": 0,
            "molist": [],
            "check_field": settings[moclass]["check_field"],
            "re": settings[moclass]["re"],
        }

    url = f'class/{moclass}.json?query-target-filter={settings[moclass]["filter"]}'

    for mo in aci.getJson(url):
        node = re.match(
            r"(topology/pod-\d+/node-\d+)/.*", mo[moclass]["attributes"]["dn"]
        ).group(1)
        if node in check_control:
            check_control[node]["cnt"] += 1
            check_control[node]["molist"].append(mo)

    for node, info in check_control.items():
        regex = False
        if info["re"]:
            regex = info["re"]
        nei_red = check_neighbor_redundancy(info["molist"], info["check_field"], regex)
        if info["cnt"] >= settings[moclass]["ok_cnt"] and nei_red:
            print_msg(
                f"{node} ({dn2hostname[node]}) has {info['cnt']} connected {settings[moclass]['msg_suffix']} to multiple neighbors"
            )
        else:
            print_msg(
                f"{node} ({dn2hostname[node]}) uplinks: {info['cnt']}, different neighbors: {nei_red}",
                False,
            )


def test_redundany():
    aci.login()

    # check if multipod fabric
    pods = len(aci.getJson("class/fabricPod.json"))
    if pods > 1:
        logging.info(f"multipod discovered, nr of pods is {pods}")
        IS_MULTIPOD = True

    # get fabric nodes
    for mo in aci.getJson("class/fabricNode.json?order-by=fabricNode.dn|asc"):
        nodes[mo["fabricNode"]["attributes"]["role"]].append(
            mo["fabricNode"]["attributes"]["dn"]
        )
        dn2hostname[mo["fabricNode"]["attributes"]["dn"]] = mo["fabricNode"][
            "attributes"
        ]["name"]

    # check apics
    check_status("lldpAdjEp")

    # checking spines
    if IS_MULTIPOD:
        check_status("ospfAdjEp")

    # checking leaf/spine uplinks
    check_status("isisAdjEp")

    aci.logout()


if __name__ == "__main__":
    test_redundany()
