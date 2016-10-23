import yaml
import copy
from collections import defaultdict
import subprocess
import re
import json

topo_dict = {}


OS_IFPREFIX = {
        "junos" : "em",
        "eos"   : "Ethernet",
        "os10"   : "ethernet1/1/"
        }

def loadYamlTopoFile(filename):
    with open(filename) as mystream:
        try:
            return yaml.load(mystream)
        except yaml.YAMLError as exc:
            print(exc)
        return None;


def getFullPortName(os, portname):
    prefix = OS_IFPREFIX[os];
    if prefix is None:
        return portname;
    else:
        return "%s%s" % (prefix,portname)

def checkFabricStatus(fabricInputFile, fabricCurrentState):
    fabricdetails = {}
    extraLldpLinks = defaultdict(dict);
    missingLinks = defaultdict(dict);
    verifiedLinks = defaultdict(dict);
    wrongLinks = defaultdict(dict);
    verifyStatus = [];

    
    for switch, ports in fabricCurrentState.items():
        for port, lldp in ports.items():
            if port not in fabricInputFile[switch]:
                extraLldpLinks[switch][port] = lldp
                continue;

            inputFileRemHost = fabricInputFile[switch][port]
            if inputFileRemHost is None:
                extraLldpLinks[switch][port] = lldp
            elif ((inputFileRemHost['host'] == lldp['host']) and
                    (inputFileRemHost['port'] == lldp['port'])):
                fabricInputFile[switch][port]['state'] = 'verified';
                verifiedLinks[switch][port] = copy.deepcopy(lldp);
            else:
                fabricInputFile[switch][port]['state'] = 'wrong';
                wrongLinks[switch][port] = { 
                        'expectedHost' : inputFileRemHost['host'],
                        'expectedPort' : inputFileRemHost['port'],
                        'currentHost'  : lldp['host'],
                        'currentPort'  : lldp['port']
                        }

    for switch, ports in fabricInputFile.items():
        for port, lldp in ports.items():
            if 'state' not in lldp:
                missingLinks[switch][port] = lldp;

    fabricdetails['verifiedLinks'] = verifiedLinks;
    fabricdetails['wrongLinks'] = wrongLinks;
    fabricdetails['extraLldpLinks'] = extraLldpLinks;
    fabricdetails['missingLinks'] = missingLinks;

    if len(wrongLinks) > 0 :
        verifyStatus.append("Wrong wiring detected in Lldp")
    if len(missingLinks) > 0 :
        verifyStatus.append("Missing Links detected")
    if len(extraLldpLinks) > 0:
        verifyStatus.append("Extra Links detected in Lldp")
    if len(verifyStatus) <= 0:
        verifyStatus.append("Netwrok Physical Topology consistent with Lldp details")
    fabricdetails['veriphystatus'] = verifyStatus;

    return fabricdetails;

def getFabricDictFromTopo(topoList):
    fabric = defaultdict(dict); 
   
    switchinfo = topoList['switchinfo'];
    linkinfo = topoList['linkinfo'];

    for host1, host2 in linkinfo.items():
        lHost = tuple ([s.lstrip() for s in host1.split(",")])
        remHost = tuple ([s.lstrip() for s in host2.split(",")])

        switch_os = switchinfo[lHost[0]]
        rem_switch_os = switchinfo[remHost[0]]

        lFullPortName = getFullPortName(switch_os, lHost[1]) 
        rFullPort = getFullPortName(rem_switch_os, remHost[1])

        fabric[lHost[0]][lFullPortName] = { "host" : remHost[0],
                    "port" : rFullPort}
        fabric[remHost[0]][rFullPort] =  { "host" : lHost[0],
                    "port" : lFullPortName}

    return fabric;

def ansible_play():
    proc = subprocess.Popen (["ansible-playbook", "-v", "facts.yaml", "-i", "switch_inventory.yaml"], stdout=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    l = re.split (r'ok: \[[a-z]+[0-9]\] => ', stdout)
    l[len(l)-1] = re.split ("\nPLAY", l[len(l)-1])[0]
    found = defaultdict(dict)
    for s in l[1:]:
        j = json.loads (s)
       
        src = j["ansible_facts"]["ansible_net_neighbors"] 
        host = j["ansible_facts"]["ansible_net_hostname"]
        for port,v in src.items():
            if port in found[host]: 
                found[host][port].update (v[0])  
            else:
                found[host][port] = v[0]  
    return found
     

if __name__ == "__main__":
    yamlLoad = loadYamlTopoFile("topo_link.yaml");
    fabricInput = getFabricDictFromTopo(yamlLoad);

    yamlLoad = loadYamlTopoFile("topo_lldp.yaml");
    fabricLldp = ansible_play()

    finalState = checkFabricStatus(fabricInput, fabricLldp);
    print json.dumps(finalState);
