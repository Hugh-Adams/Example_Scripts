#!/usr/bin/env python

import requests
import json
import grpc
from google.protobuf import wrappers_pb2 as wrappers

# import the inventory models and services
from arista.inventory.v1 import models
from arista.inventory.v1 import services

CV_HOST = "ctl1-cvp-server-002"
CV_API_PORT = "8443"
USERNAME = "cvpadmin"
PASSWORD = "ardvark"
TOKEN_FILE = "./ctl1-cvp-server-002_token.txt"
#TOKEN_FILE = None
CERT_FILE = "./ctl1-cvp-server-002_cvp.crt"
#CERT_FILE = None
DEVICE_NAME = "CTL1-PRD-SLEAF-001"
DEVICE_ID = "D433C4C068738C68495CB47E749FAE33"
RPC_TIMEOUT = 30  # in seconds

if TOKEN_FILE:
    print(f"\nUsing local Token: {TOKEN_FILE}\n")
    with open(TOKEN_FILE, "r") as token_file:
        token = token_file.read().strip()
        call_credentials = grpc.access_token_call_credentials(token)
else:
    print(f"\nFetching Token from : {CV_HOST}\n")
    response = requests.post('https://' + CV_HOST + '/cvpservice/login/authenticate.do',
                             auth=(USERNAME, PASSWORD), verify=False)
    call_credentials = grpc.access_token_call_credentials(response.json()['sessionId'])

if CERT_FILE:
    print(f"\nUsing local Cert File: {CERT_FILE}\n")
    with open(CERT_FILE, "rb") as cert_file:
        cert = cert_file.read()
        channel_credentials = grpc.ssl_channel_credentials(root_certificates=cert)
else:
    print(f"\nNo Cert File avaiable\n")
    channel_credentials = grpc.ssl_channel_credentials()

combined_credentials = grpc.composite_channel_credentials(channel_credentials, call_credentials)
channel = grpc.secure_channel(CV_HOST + ':' + CV_API_PORT, combined_credentials)
stub = services.DeviceServiceStub(channel)

# create a unary device request, setting the key to the given serial
#req = services.DeviceRequest(key={"device_id": wrappers.StringValue(value=DEVICE_ID)})
# issue the request and print it
#resp = stub.GetOne(req)
#print(f"\n\n{DEVICE_NAME}:{resp}\n\n")


 # create a stream request
get_all_devices = services.DeviceStreamRequest()

# must match a Device where streaming_status = ACTIVE
get_all_devices.partial_eq_filter.append(models.Device(streaming_status=models.STREAMING_STATUS_ACTIVE,))

total_devices = 0
# make the GetAll request and loop over the streamed responses
for resp in stub.GetAll(get_all_devices, timeout=RPC_TIMEOUT):
    # print {hostname}: {serial}
    print(f"{resp.value.hostname.value:<25}{resp.value.key.device_id.value:<25}")
    total_devices += 1
print("{} matching devices in inventory".format(total_devices))

