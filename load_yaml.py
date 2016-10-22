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
    for switchname, value in linkinfo.items():
        fabric[switchname] = {};

        switch_ports = value['ports']
        switch_os = switchinfo[switchname]

        for portname, value in switch_ports.items():
            localFullPortName = getFullPortName(switch_os, portname) 
            rem_switch_os = switchinfo[value['host']]
            fullport = getFullPortName(rem_switch_os, portname)
            value['port'] = fullport
            print "[%s - %s] ---> %s - %s " % (switchname, localFullPortName, value['host'], value['port'])
            fabric[switchname][localFullPortName] = copy.deepcopy(value);
            fabric[value['host']][value['port']] =  { "host" : switchname,
                    "port" : localFullPortName}

    return fabric;

if __name__ == "__main__":
    #fabric = getFabricDictFromTopo(yamlLoad);
    #yamlLoad = loadYamlTopoFile("topology.yaml");
    yamlLoad = loadYamlTopoFile("topo_link.yaml");
    fabric = getFabricDictFromTupleTopo(yamlLoad);
    print yamlLoad
    #print fabric

