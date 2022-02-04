#!/usr/bin/env python3
#
# Copyright (c) 2021, Arista Networks, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#  - Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#  - Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#  - Neither the name of Arista Networks nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Make a copy of the Events Configured in CloudVision
# and Update the Custom Events in CloudVision
#
#    Written by:
#       Hugh Adams, Arista Networks
# 
#
# Requires a user with read access to the CVP aeris database
# Requires:
#      --src      CV Server IP or URL :8443
#      --srcauth  token,token1.txt,cvp1.crt
#      --device   Comma separated device serial number list
#
# Usage:
# decomm_device.py --src=10.83.12.79:8443 --srcauth=token,src_token.txt,src_cvp.crt 
#      --device deviceSN1,deviceSN2

import os, sys, re
from google.protobuf.timestamp_pb2 import Timestamp
from cloudvision.Connector.grpc_client import GRPCClient, create_query, create_notification
from cloudvision.Connector.codec.custom_types import FrozenDict
from cloudvision.Connector.codec import Wildcard, Path
from utils import *
from cv_parser import add_arguments
import json
import argparse

debug = False


def get_client(apiserverAddr, token=None, certs=None, key=None, ca=None):
    ''' Returns the gRPC client used for authentication'''
    return GRPCClient(apiserverAddr, token=token, key=key, ca=ca, certs=certs)


def get(client, dataset, pathElts):
    ''' Returns a query on a path element'''
    result = {}
    query = [
        create_query([(pathElts, [])], dataset)
    ]
    for batch in client.get(query):
        for notif in batch["notifications"]:
            if debug:
                pretty_print(notif["updates"])
            result.update(notif["updates"])
    return result


def unfreeze(o):
    ''' Used to unfreeze Frozen dictionaries'''
    if isinstance(o, (dict, FrozenDict)):
        return dict({k: unfreeze(v) for k, v in o.items()})
    if isinstance(o, (str)):
        return o
    try:
        return [unfreeze(i) for i in o]
    except TypeError:
        pass
    return o


def publish(client, dataset, pathElts, data={}):
    ''' Publish function used to update specific paths in the database'''
    ts = Timestamp()
    ts.GetCurrentTime()

    # Boilerplate values for dtype, sync, and compare
    dtype = "analytics"
    sync = True
    compare = None
    updates = []
    for dataKey in data.keys():
        dataValue = data.get(dataKey)
        updates.append((dataKey, dataValue))

    notifs = [create_notification(ts, pathElts, updates=updates)]
    client.publish(dtype=dtype, dId=dataset, sync=sync, compare=compare, notifs=notifs)
    return 0


if __name__ == "__main__":
    filepath = str(os.path.abspath(os.path.dirname(sys.argv[0])))+'/'
    ds = ("Decommission Device in a CV cluster\n"
          "Usage:\n"
          "\t decomm_device.py --src=10.83.12.79:8443 --srcauth=token,src_token.txt,src_cvp.crt --device deviceSN1,deviceSN2\n"
          )
    base = argparse.ArgumentParser(description=ds,
                                   formatter_class=argparse.RawTextHelpFormatter)
    add_arguments(base)
    args = base.parse_args()

    if args.device.lower() != "NotSet":
        # Only set "proceed" True if all required checks are passed
        proceed = False
        if args.src != 'NotSet' and args.srcauth != 'NotSet':
            # Check for a TCP port definition in src address
            if ':' in args.src:
                # Authenticate to the CVP server
                client = get_client(args.src, certs=args.certFileSrc, key=args.keyFileSrc,
                            token=args.tokenFileSrc, ca=args.caFileSrc)
                proceed = True
            else:
                proceed = False
                print(f'\nThe src option is missing a port - {args.dst}\n')
        else:
            proceed = False
            print('\nThe CV details (src/srcauth) are missing:\n')
            print(f'src: {args.src}\nsrcauth: {args.srcauth}\n')
        
        # Create deviceList and find device key in CVP
        if proceed:
            if (args.device[0] == args.devicet[-1]) and args.device.startswith(("'", '"')):
                args.device = args.device[1:-1]
            if "," in args.device:
                deviceList = re.split(',',args.device)
            else:
                deviceList =[args.device]

        if proceed:
            # "proceed" is True if all required checks were passed
            # decomm devices on Target CVP
            dataset = "analytics" # CV data set 
            # Iterate through the device provided
            # and publish the decomm path to the database
            for device in deviceList:
                pathElts = "/DatasetInfo/Manual/Decommission" #Decommission Device PAth
                custom_data = device
                publish(client, dataset, pathElts, custom_data)
        else:
            print(f'The details for the device names provided could not be found {args.device}')
        if proceed:
            print(f'\ncopy_custom_events.py mode: {args.mode} - completed')
        else:
            print(f'\n{ds}')
    else:
        print(f'Invalid Device List: "{args.device}" please provide a comma separated device list')