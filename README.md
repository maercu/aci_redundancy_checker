# ACI Redundancy Checker

## Overview

This script is useful during upgrades of an ACI-fabric - the follwing is checked:
 - Number of active fabric uplinks per controller
 - Number of OSPF active neighbors in VRF overlay-1 on the spines (multipod fabric only)
 - Number of active ISIS neighbors per leaf

### Sample output

![Sample Output](/images/sample_output.png?raw=true)

## Installation

### Clone repo

    git clone https://github.com/maercu/aci_redundancy_checker.git

### Create Pyton venv and install dependencies

    cd aci_redundancy_checker
    python3 -m venv .venv
    source .venv/bin/activate

### Load APIC credentials envioronment variables  
    
    cat << EOF > acienv 
    export ACI_USER=username
    export ACI_PASS=password
    export ACI_HOST=hostname_or_ip
    EOF

    source acienv

### Start the script

    python test_redundancy.py
