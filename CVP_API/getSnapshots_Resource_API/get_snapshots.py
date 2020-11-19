#!/usr/bin/env python
#
# Copyright (c) 2020, Arista Networks, Inc.
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
# Displays Snapshots results for CVP 2020.x.x
#
#    Version 0.1 19/11/20
#
#    Written by:
#       Tamas Plugor / Hugh Adams, Arista Networks
#
#    Revision history:
#       0.1 - 19/11/2020 - initial script
#
# Requires CVP session credentials from get_token.py
#

from cloudvision.Connector.grpc_client import GRPCClient, create_query
from cloudvision.Connector.codec import Wildcard
from utils import pretty_print
from parser import base


def main(apiserverAddr, token=None, cert=None, key=None, ca=None):
    pathElts = [
        "snapshots",
        "status"
    ]
    dataSet = "cvp"
    query = [
        create_query([(pathElts, [])], dataSet)
    ]
    snapshot_ids = []

    with GRPCClient(apiserverAddr, certs=cert, key=key,
                    token=token, ca=ca) as client:
        for batch in client.get(query):
            print("Get Snapshot IDs from {}".format(apiserverAddr))
            for item in batch["notifications"]:
                print(list(item['updates'])[0])
                snapshot_ids.append(list(item['updates'])[0])

    with GRPCClient(apiserverAddr, certs=cert, key=key,
                    token=token, ca=ca) as client:
        print ("Get Snapshot Results for Snapshot ID list")
        for i in snapshot_ids:
            pathElts = ["snapshots", "status", i,
                        "snapshots", "ids", Wildcard()]
            dataSet = "cvp"
            query = [create_query([(pathElts, [])], dataSet)]
            for batch in client.get(query):
                for item in batch["notifications"]:
                    pretty_print(item['updates'])

    return 0


if __name__ == "__main__":
    args = base.parse_args()
    exit(main(args.apiserver, cert=args.certFile,
              key=args.keyFile, token=args.tokenFile, ca=args.caFile))
