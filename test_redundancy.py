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


def print_title(title):
    print(f"{fontcolors['INFO']}" + "=" * 60)
    print(f"{fontcolors['INFO']} {title}")
    print(f"{fontcolors['INFO']}" + "=" * 60)


def print_msg(msg, ok=True):
    if ok:
        print(f"{fontcolors['OK']}OK: {msg}")
    else:
        print(f"{fontcolors['FAIL']}ERROR: {msg}")


def check_status(moclass):
    settings = {
        "cnwPhysIf": {
            "title": "checking apic uplinks",
            "nodetype": "controller",
            "filter1": ("wcard", "name", "eth2-"),
            "filter2": ("eq", "operSt", "up"),
            "ok_cnt": 2,
            "msg_suffix": "fabric uplink(s)",
        },
        "ospfAdjEp": {
            "title": "checking multipod uplinks",
            "nodetype": "spine",
            "filter1": ("wcard", "dn", "dom-overlay-1"),
            "filter2": ("eq", "operSt", "full"),
            "ok_cnt": 1,
            "msg_suffix": "IPN neighbor(s)",
        },
        "isisAdjEp": {
            "title": "checking leaf uplinks",
            "nodetype": "leaf",
            "filter1": ("wcard", "dn", "dom-overlay-1"),
            "filter2": ("eq", "operSt", "up"),
            "ok_cnt": 2,
            "msg_suffix": "ISIS neighbor(s)",
        },
    }

    print_title(settings[moclass]["title"])

    check_control = {}
    for node in nodes[settings[moclass]["nodetype"]]:
        check_control[node] = 0

    url = f'class/{moclass}.json?query-target-filter=and({settings[moclass]["filter1"][0]}({moclass}.{settings[moclass]["filter1"][1]},"{settings[moclass]["filter1"][2]}"),{settings[moclass]["filter2"][0]}({moclass}.{settings[moclass]["filter2"][1]},"{settings[moclass]["filter2"][2]}"))'
    for mo in aci.getJson(url):
        node = re.match(
            r"(topology/pod-\d+/node-\d+)/.*", mo[moclass]["attributes"]["dn"]
        ).group(1)
        if node in check_control:
            check_control[node] += 1

    for node, nr in check_control.items():
        if nr >= settings[moclass]["ok_cnt"]:
            print_msg(
                f"{node} has {nr} connected {settings[moclass]['msg_suffix']}"
            )
        else:
            print_msg(
                f"{node} has {nr} connected {settings[moclass]['msg_suffix']}",
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

    # check apics
    check_status("cnwPhysIf")

    # checking spines
    if IS_MULTIPOD:
        check_status("ospfAdjEp")

    # checking leaf/spine uplinks
    check_status("isisAdjEp")

    aci.logout()


if __name__ == "__main__":
    test_redundany()
