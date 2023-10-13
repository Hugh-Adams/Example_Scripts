"""
pygnmi script
"""
from pygnmi.client import gNMIclient

TELEMETRY_REQUEST = {
                         'subscription': [
                             {
                                 'path': '/inventory/state/device/device-id'
                             }
                         ],
                         'mode': 'once',
                         'encoding': 'json'
                     }

with open("token.tok") as f:
    TOKEN = f.read().strip('\n')

if __name__ == "__main__":
     with gNMIclient(target=('192.168.0.5', '443'), token=TOKEN, skip_verify=True) as gconn:
         inventory = gconn.subscribe2(subscribe=TELEMETRY_REQUEST)
         for device in inventory:
                print(device)



gnmi -a 192.168.0.5:443 subscribe --path "openconfig:/interfaces/interface/state/counters" --token=$token --target=device_id --skip-verify

gnmi -addr=192.168.0.5:443 -token=`cat token.tok` -mode=stream subscribe origin=openconfig target=spine1 /interfaces/interface/state/admin-status

gnmi -addr 192.168.0.5:44 -username arista -password arista subscribe '/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state'



Get interfaces status of a device at a specific time

gnmi -addr=192.168.0.5:443 -token=`cat token.tok` -mode=once -history_snapshot=2022-07-17T12:47:00Z subscribe origin=openconfig target=spine1 "/interfaces/interface[name=Ethernet2]/state/admin-status"

Get interface status of a device at a specified time range

gnmi -addr=192.0.2.100:443 -token=`cat token.tok` -mode=stream -history_start=2021-07-13T09:47:00Z -history_end=2021-07-13T09:51:00Z subscribe origin=openconfig target=JPE17471508 "/interfaces/interface[name=Ethernet47]/state/admin-status"
