import yaml
import copy
from collections import defaultdict

topo_dict = {}


OS_IFPREFIX = {
        "junos" : "em",
        "eos"   : "Ethernet"
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

if __name__ == "__main__":
    yamlLoad = loadYamlTopoFile("topo_link.yaml");
    fabric = getFabricDictFromTopo(yamlLoad);
    for key, value in fabric.items():
        print key
        print value

