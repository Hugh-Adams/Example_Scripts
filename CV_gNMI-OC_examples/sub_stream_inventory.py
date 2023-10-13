"""
pygnmi script
"""

from pygnmi.client import gNMIclient

TELEMETRY_REQUEST = {
                         'subscription': [
                             {
                                 'path': '/inventory/state/device/device-id',
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
        inventory = gconn.subscribe2(subscribe=TELEMETRY_REQUEST)
        for device in inventory:
            print(device)

