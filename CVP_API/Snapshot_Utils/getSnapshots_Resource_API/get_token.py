#!/usr/bin/env python
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
# Fetches a session token and optional SSL certificate from CVP 2020.x.x
# Useful when authenticating in the included examples.
#
#    Version 0.1 10/2020
#
#    Written by:
#      Arista Networks
#
#    Revision history:
#       0.1 - 10/2020 - initial script
#
# Requires CVP user credentials
#

import argparse
import requests
import ssl

def main(args):
    r = requests.post('https://' + args.server + '/cvpservice/login/authenticate.do',
                      auth=(args.username, args.password), verify=args.ssl is False)

    r.json()['sessionId']

    with open("token.txt", "w") as f:
        f.write(r.json()['sessionId'])

    if args.ssl:
        with open("cvp.crt", "w") as f:
            f.write(ssl.get_server_certificate((args.server, 443)))


if __name__ == '__main__':
    ds = ("Get a session token (and optional SSL cert) from CVP and store to token.txt")
    parser = argparse.ArgumentParser(
        description=ds,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        '--server',
        required=True,
        help="CloudVision server to connect to in <host> format.")
    parser.add_argument("--username", required=True, type=str,
                        help="Username to authorize with")
    parser.add_argument("--password", required=True, type=str,
                        help="Password to authorize with")
    parser.add_argument("--ssl", action="store_true",
                        help="Save the self-signed certificate to cvp.crt")

    args = parser.parse_args()
    main(args)
