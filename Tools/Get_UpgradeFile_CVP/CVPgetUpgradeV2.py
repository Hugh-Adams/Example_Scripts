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
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ARISTA NETWORKS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# CVPgetUpgrade.py
#
#    Written by:
#       Hugh Adams, Arista Networks
#
"""
DESCRIPTION
A Python script for fetching the required upgrade file
from www.arista.com.
Arguments for the Command Line:
    upgrade - CloudVision Upgrade file name i.e. cvp-upgrade-2020.2.3.tgz
    token   - User API access token found at https://www.arista.com/en/users/profile
The script should not need any additional packages installed on CVP
"""
__author__ = 'Arista Networks'

import base64
import json
import warnings
import requests
import argparse
import sys
import os

def main (args):
    '''
    args.upgrade - CloudVision Upgrade file name i.e. cvp-upgrade-2020.2.3.tgz
    args.token   - User API access token found at https://www.arista.com/en/users/profile
    '''

    # Create the Various Paths for the files
    filePath = '/support/download/CloudVision/CloudVision Portal/Active Releases/'
    fileParts=str(args.upgrade.split('-')[-1]).split('.')
    # Create Folder Path
    # Major Release
    upgradeFile=str(fileParts[0])+"."+str(fileParts[1])+"/"
    # Release Revision
    upgradeFile=upgradeFile+str(fileParts[0])+"."+str(fileParts[1])+"."+str(fileParts[2])+"/"
    # File Name
    upgradeFile=upgradeFile+args.upgrade
    # Create Download URL
    url = filePath+upgradeFile
    if args.test:
        saveFile = str(os.path.abspath(os.path.dirname(sys.argv[0])))+"/"+args.upgrade
    else:
        saveFile = "/tmp/upgrade/"+args.upgrade
        try:
            os.makedirs("/tmp/upgrade/")
        except OSError:
            # directory already exists
            pass
    
    # Access the Arista Website
    # Step 1 - get a session code
    warnings.filterwarnings("ignore")
    creds = (base64.b64encode(args.token.encode())).decode("utf-8")
    session = requests.Session()
    # Set up proxy server if required
    if args.proxyAddr is not None:
        proxies = { str(args.proxyType):str(args.proxyAddr)}
        session.proxies.update(proxies)

    session_code_url = "https://www.arista.com/custom_data/api/cvp/getSessionCode/"
    jsonpost = {'accessToken': creds}
    result = session.post(session_code_url, data=json.dumps(jsonpost))
    if result.json()["status"]["message"] == 'Access token expired':
        print("The API token has expired. Please visit arista.com, click on your profile and select Regenerate Token then re-run the script with the new token.")
        sys.exit()
    elif result.json()["status"]["message"] == 'Invalid access token':
        print("The API token is incorrect. Please visit arista.com, click on your profile and check the Access Token. Then re-run the script with the correct token.")
        sys.exit()
    session_code = (result.json()["data"]["session_code"])
    

    warnings.filterwarnings("ignore")
    jsonpost = {'token_auth': creds}

    # Step 2 - use the path and session code to get the actual direct download link URL
    download_link_url = "https://www.arista.com/custom_data/api/cvp/getDownloadLink/"
    jsonpost = {'sessionCode': session_code, 'filePath': url}
    result = session.post(download_link_url, data=json.dumps(jsonpost))
    download_link = (result.json()["data"]["url"])
    if args.test:
        print ("Server Response: %s\nResponse Data: %s}" %(result,result.json()))
    
    if not args.nofile:
        # Download the file
        chunkSize = 1024
        r = session.get(download_link, stream=True)
        with open(saveFile, 'wb') as fh:
            for chunk in r.iter_content(chunk_size=chunkSize): 
                if chunk: # filter out keep-alive new chunks
                    fh.write(chunk)

        print(result)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--upgrade', required=True,
                        help="CloudVision Upgrade File Name i.e. cvp-upgrade-2020.2.3.tgz")
    parser.add_argument('--token', required=True, help="User API access token found at https://www.arista.com/en/users/profile")
    parser.add_argument('--proxyType', required=False, help="Type of proxy http or https")
    parser.add_argument('--proxyAddr', required=False, help="IP address or URL of proxy server", default=None)
    parser.add_argument('--test', required=False, action='store_true')
    parser.add_argument('--nofile', required=False, action='store_true')
    args = parser.parse_args()
    main(args)
