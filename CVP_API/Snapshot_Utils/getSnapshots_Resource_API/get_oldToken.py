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

# Import Required Libraries
import argparse
import requests
import ssl
import json
from requests import packages


# CVP manipulation class
# Set up classes to interact with CVP API
# serverCVP exception class
class serverCvpError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

# Create a session to the CVP server
class serverCvp(object):

    def __init__(self, HOST, USER, PASS):
        self.url = "https://%s" % HOST
        self.authenticateData = {'userId': USER, 'password': PASS}
        requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:ECDH+3DES:DH+3DES:RSA+AESGCM:RSA+AES:RSA+3DES:!aNULL:!MD5:!DSS'
        from requests.packages.urllib3.exceptions import InsecureRequestWarning
        try:
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        except packages.urllib3.exceptions.ProtocolError as e:
            if str(e) == "('Connection aborted.', gaierror(8, 'nodename nor servname provided, or not known'))":
                raise serverCvpError(
                    "DNS Error: The CVP Server %s can not be found" % HOST)
            elif str(e) == "('Connection aborted.', error(54, 'Connection reset by peer'))":
                raise serverCvpError("Error, connection aborted")
            else:
                raise serverCvpError("Could not connect to Server")

    def logOn(self):
        try:
            headers = {'Content-Type': 'application/json'}
            loginURL = "/web/login/authenticate.do"
            self.response = requests.post(
                self.url+loginURL, json=self.authenticateData, headers=headers, verify=False)
            if "errorMessage" in str(self.response.json()):
                text = "Error log on failed: %s" % self.response.json()[
                    'errorMessage']
                raise serverCvpError(text)
        except requests.HTTPError as e:
            raise serverCvpError(
                "Error HTTP session to CVP Server: %s" % str(e))
        except requests.exceptions.ConnectionError as e:
            raise serverCvpError("Error connecting to CVP Server: %s" % str(e))
        except:
            raise serverCvpError("Error in session to CVP Server")
        self.cookies = self.response.cookies
        return self.response.json()

    def certs(self,sslCheck):
        with open("token.txt", "w") as f:
            f.write(self.response.json()['sessionId'])
        if sslCheck:
            with open("cvp.crt", "w") as f:
                f.write(ssl.get_server_certificate((args.server, 443)))

    def logOut(self):
        headers = {'Content-Type': 'application/json'}
        logoutURL = "/cvpservice/login/logout.do"
        response = requests.post(self.url+logoutURL, cookies=self.cookies,
                                 json=self.authenticateData, headers=headers, verify=False)
        return response.json()


def main(args):
    print (f"Attaching to {args.server}...")
    try:
        cvpSession = serverCvp(args.server, args.username, args.password)
        logOn = cvpSession.logOn()
    except serverCvpError as e:
        text = "Login Problem- %s" % e.value
        print (text)
    print ("Login Complete")
    print ("\nFetching Certs...")
    try:
        cvpSession.certs(args.sslCheck)
    except serverCvpError as e:
        text = "Cert Fetch Problem- %s" % e.value
        print (text)
    print ("Fetch Certs Complete")
    print (f"Log Off from {args.server}")
    try:
        cvpSession.logOut()
    except serverCvpError as e:
        text = "Log Off Problem- %s" % e.value
        print(text)
    print ("Done")
    


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
    parser.add_argument("--sslCheck", action="store_true",
                        help="Save the self-signed certificate to cvp.crt")

    args = parser.parse_args()
    main(args)
