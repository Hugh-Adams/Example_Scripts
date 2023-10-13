"""
pygnmi script
"""

from pygnmi.client import gNMIclient

TELEMETRY_REQUEST = {
                         'subscription': [
                             {
                                #'path': 'openconfig:/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state',
                                 'path': 'openconfig:/network-instances/network-instance[name=default]/protocols/protocol[identifier=BGP][name=BGP]/bgp/neighbors/neighbor[neighbor-address=172.16.0.5]/state/session-state',
                                 'mode': 'target_defined'
                             }
                         ],
                         'mode': 'stream',
                         'encoding': 'json'
                     }

with open("token.tok") as f:
    TOKEN = f.read().strip('\n')

if __name__ == "__main__":
    with gNMIclient(target=('192.168.0.5', '443'), token=TOKEN, skip_verify=True) as gconn:
        gconn.capabilities()
        for item in gconn.subscribe2(subscribe=TELEMETRY_REQUEST, target="spine1"): 
                print(item)

