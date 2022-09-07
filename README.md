# ACI Redundancy Checker

## Overview

This script is useful during upgrades of an ACI-fabric - the follwing is checked:
 - Number of active fabric uplinks per controller
 - Number of active OSPF neighbors in VRF overlay-1 on the spines (multipod fabric only)
 - Number of active ISIS neighbors per leaf

### Sample output

![Sample Output](/images/sample_output.png?raw=true)

## Installation/Usage

### Clone repo

    git clone https://github.com/maercu/aci_redundancy_checker.git

### Option A - Docker
    cd aci_redundancy_checker
    docker build -t aciredtest .
    docker run --rm -e ACI_HOST=hostname_or_ip -e ACI_USER=user -e ACI_PASS=password aciredtest

### Option B - Run in venv

#### Create Pyton venv and install dependencies

    cd aci_redundancy_checker
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

#### Load APIC credentials envioronment variables  
    
    tee acienv << EOF
    export ACI_USER=username
    export ACI_PASS=password
    export ACI_HOST=hostname_or_ip
    EOF

    source acienv

#### Start the script

    python test_redundancy.py
