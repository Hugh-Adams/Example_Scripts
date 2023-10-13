'''
This script uses RESTCONF to get the admin-status of the interface Ethernet6 of leaf1
'''

import json
import requests

requests.packages.urllib3.disable_warnings()

with open("token.tok") as f:
    token = f.read().strip('\n')

headers = {
  'Accept': 'application/json',
  'Cookie': "access_token=" + token
}

DEVICE_SN = 'leaf1'

URL = "https://192.168.0.5/restconf/data/interfaces/interface[name=Ethernet6]/state/admin-status?arista-target=" + DEVICE_SN + "&arista-origin=openconfig"

response = requests.request("GET", URL, headers=headers,  verify=False)
response.json()
