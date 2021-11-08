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
#       Tamas Plugar, Arista Networks
#       Hugh Adams, Arista Networks
#
# Requires a user with read access to the CVP aeris database
# Requires:
#      --mode     get (read Events from CV), set (Update Custom Events on CV), sync (copy events between CV clusters)
#      --src      CV Server IP or URL :8443
#      --srcauth  token,token1.txt,cvp1.crt
#      --dst      CV Server IP or URL :8443
#      --dstauth  token,token1.txt,cvp1.crt
#
# Usage:
# copy_custom_events.py --mode sync --src=10.83.12.79:8443 --srcauth=token,src_token.txt,src_cvp.crt 
#      --dst=10.83.12.79:8443 --dstauth=token,dst_token.txt,dst_cvp.crt

import os, sys
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


def getTurbinesConfigs(client):
    ''' Returns all turbine config pointers'''
    pathElts = [
        "Turbines",
        "config"
    ]
    dataset = "analytics"
    return get(client, dataset, pathElts)


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


def getEventTurbineNames(client):
    ''' Returns the name of all turbines that generate events'''
    turbine_cfg = getTurbinesConfigs(client)
    event_names = []
    for i in turbine_cfg.keys():
        if "event" in i:
            event_names.append(i)
    return event_names


def getEventsCfg(client):
    ''' Gets the configuration data of each event turbine'''
    event_names = getEventTurbineNames(client)

    dataset = "analytics"
    event_config = {}

    for event in event_names:
        # Initialize the event dictionary where the default and custom rules
        # along with the path elements for each type will be stored
        event_dict = {}
        event_dict['default'] = {"path_elements": [], "updates": {}}
        pathElts = [
            "Turbines",
            "config",
            event,
            Wildcard()
        ]
        query = [create_query([(pathElts, [])], dataset)]
        for batch in client.get(query):
            for notif in batch["notifications"]:
                # Only build a dictionary for custom rules if the custom key exists
                if "custom" in notif['path_elements']:
                    if "custom" in event_dict.keys():
                        event_dict['custom']["updates"].update(notif['updates'])
                        event_dict['custom']["path_elements"] = notif['path_elements']
                    else:
                        event_dict['custom'] = {"path_elements": [], "updates": {}}
                        event_dict['custom']["updates"].update(notif['updates'])
                        event_dict['custom']["path_elements"] = notif['path_elements']
                if "default" in notif['path_elements']:
                    event_dict['default']["updates"].update(notif['updates'])
                    event_dict['default']["path_elements"] = notif['path_elements']
        event_config[event] = event_dict
    return unfreeze(event_config)


def publish(client, dataset, pathElts, data={}):
    ''' Publish function used to update specific paths in the database'''
    ts = Timestamp()
    ts.GetCurrentTime()

    # Boilerplate values for dtype, sync, and compare
    dtype = "device"
    sync = True
    compare = None
    updates = []
    for dataKey in data.keys():
        dataValue = data.get(dataKey)
        updates.append((dataKey, dataValue))

    notifs = [create_notification(ts, pathElts, updates=updates)]
    client.publish(dtype=dtype, dId=dataset, sync=sync, compare=compare, notifs=notifs)
    return 0


def backupConfig(filepath,serverType, data):
    ''' Saves data in a json file'''
    filename = "backup_" + str(serverType) + ".json"
    fullpath = filepath+filename
    fileWrite(fullpath, data, 'json','w')


if __name__ == "__main__":
    filepath = str(os.path.abspath(os.path.dirname(sys.argv[0])))+'/'
    ds = ("Backup and/or Copy CVP Event Generation Configuration between CV clusters\n"
          "Usage:\n"
          "\t copy_custom_events.py --mode get --src=10.83.12.79:8443 --srcauth=token,src_token.txt,src_cvp.crt\n"
          "\t copy_custom_events.py --mode set --dst=10.83.12.79:8443 --dstauth=token,dst_token.txt,dst_cvp.crt\n"
          "\t copy_custom_events.py --mode sync --src=10.83.12.79:8443 --srcauth=token,src_token.txt,src_cvp.crt\n"
          "\t      --dst=10.83.12.79:8443 --dstauth=token,dst_token.txt,dst_cvp.crt\n"
          )
    base = argparse.ArgumentParser(description=ds,
                                   formatter_class=argparse.RawTextHelpFormatter)
    add_arguments(base)
    args = base.parse_args()

    if args.mode.lower() in ['get','set','sync']:
        # Only set "proceed" True if all required checks are passed
        proceed = False
        if args.mode.lower() in ['get','sync']:
            if args.src != 'NotSet' and args.srcauth != 'NotSet':
                # Check for a TCP port definition in src address
                if ':' in args.src:
                    # Authenticate to the Source CVP server
                    SRCclient = get_client(args.src, certs=args.certFile, key=args.keyFile,
                                token=args.tokenFile, ca=args.caFile)
                    # Get the Events from CloudVision
                    src_config = getEventsCfg(SRCclient)
                    # backup the event configurations from CloudVision
                    # #    - backupSourceCVP.json
                    backupConfig(filepath, 'Source_CVP', src_config)
                    proceed = True
                else:
                    proceed = False
                    print(f'\nThe "mode" option was either "get" or "sync" \nbut the src option is missing a port - {args.src}\n')
            else:
                proceed = False
                print('\nThe "mode" option was either "get" or "sync"\nbut Source CV details (src/srcauth) are missing:\n')
                print(f'src: {args.src}\nsrcauth: {args.srcauth}\n')

        if args.mode.lower() in ['set','sync']:
            if args.dst != 'NotSet' and args.dstauth != 'NotSet':
                # Check for a TCP port definition in src address
                if ':' in args.dst:
                    # Authenticate to the Destination CVP server
                    DSTclient = get_client(args.dst, certs=args.certFileDst, key=args.keyFileDst,
                                token=args.tokenFileDst, ca=args.caFileDst)
                    # Get the Events from CloudVision
                    dst_config = getEventsCfg(DSTclient)
                    # backup the event configurations from CloudVision
                    #   - backupSourceCVP.json
                    backupConfig(filepath, 'Destination_CVP', dst_config)
                    proceed = True
                else:
                    proceed = False
                    print(f'\nThe "mode" option was either "set" or "sync"\nbut the dst option is missing a port - {args.dst}\n')
            else:
                proceed = False
                print('\nThe "mode" option was either "set" or "sync" \nbut Destination CV details (dst/dstauth) are missing:\n')
                print(f'dst: {args.dst}\ndstauth: {args.dstauth}\n')

        if args.mode.lower() in ['set','syn'] and proceed:
            # "proceed" is True if all required checks were passed
            source_config = fileOpen(filepath+'backup_Source_CVP.json', 'json')
            # Apply Custom Events to Target CVP
            dataset = "analytics"
            # Iterate through the custom events from the source CVP server
            # and publish the data and the pointer to that data
            if source_config:
                for events in source_config:
                    if "custom" in source_config[events].keys():
                        pathElts = source_config[events]["custom"]["path_elements"]
                        custom_data = source_config[events]["custom"]["updates"]
                        publish(DSTclient, dataset, pathElts, custom_data)
                        # path pointers need to be created with a different encoding
                        # they are optional to have, but
                        ptr_data = {"custom": Path(keys=["Turbines", "config", events, "custom"])}
                        publish(DSTclient, dataset, pathElts[:-1], ptr_data)
            else:
                print(f'The source file for the "set" option {filepath}backup_Source_CVP.json was not found, no changes made')
        if proceed:
            print(f'\ncopy_custom_events.py mode: {args.mode} - completed')
        else:
            print(f'\n{ds}')
    else:
        print(f'Invalid Action: "{args.mode}" please choose --mode get, --mode set, or --mode sync')