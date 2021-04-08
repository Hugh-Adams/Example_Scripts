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
# Synchronize Configlets between two instances of CVP
# Backups of each Configlet set will be
#
#    Version 0.1 07/04/2021
#
#    Written by:
#       Hugh Adams, Arista Networks
#
#    Revision history:
#       0.1 - 07/04/2021 - initial script
#
# Requires a user with read/write access to CVP provisioning/configlets 
#
# Requires:
#      --server    CloudVision server url or IP address
#      --user      CloudVision User Name
#      --passwd    User's Password
#
# Optional:
#      --filter     Partial Configlet name match to filter Sync operation on
#      --overwrite  Default action to update both matching configlets to latest (date/time)
#                   overwrite will push first CVP configlet configs to second CVP and overwrite
#
#
#


# Import Required Libraries
import json
import requests
import os, sys
import argparse
from tqdm import tqdm

class serverCvpError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

# Create a session to the CVP server
class serverCvp(object):

    def __init__(self, HOST, USER, PASS):
        self.host = HOST
        self.url = "https://%s" % HOST
        self.authenticateData = {'userId': USER, 'password': PASS}
        requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:ECDH+3DES:DH+3DES:RSA+AESGCM:RSA+AES:RSA+3DES:!aNULL:!MD5:!DSS'
        from requests.packages.urllib3.exceptions import InsecureRequestWarning
        try:
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        except packages.urllib3.exceptions.ProtocolError as e:
            if str(e) == "('Connection aborted.', gaierror(8, 'nodename nor servname provided, or not known'))":
                raise serverCvpError("Error: %s can not be found" % HOST)
            elif str(e) == "('Connection aborted.', error(54, 'Connection reset by peer'))":
                raise serverCvpError("Error: %s connection aborted" %HOST)
            else:
                raise serverCvpError("Error: %s could not connect" %HOST)

    def logOn(self):
        try:
            URL = "/web/login/authenticate.do"
            headers = {'Content-Type': 'application/json'}
            response = requests.post(self.url+URL, json=self.authenticateData, 
                headers=headers, verify=False)
            if "errorMessage" in str(response.json()):
                text = "Error log on failed: %s" % response.json()[
                    'errorMessage']
                raise serverCvpError(text)
        except requests.HTTPError as e:
            raise serverCvpError("Error: session to %s : %s" %(self.host,str(e)))
        except requests.exceptions.ConnectionError as e:
            raise serverCvpError("Error: connecting to %s : %s" %(self.host,str(e)))
        except:
            raise serverCvpError("Error: session to %s failed" %self.host)
        self.cookies = response.cookies
        return response.json()

    def logOut(self):
        URL = "/cvpservice/login/logout.do"
        headers = {'Content-Type': 'application/json'}
        response = requests.post(self.url+URL, cookies=self.cookies, 
            headers=headers, verify=False)
        return response.json()

    def configlets_get(self, cType="All"):
        """ Return a list of configlets matching configlet type cType:
               Configlet - Returns static and generated configlets
               Builder - Returns builder as well as draft configlets
               Draft - Returns draft configlets
               BuilderWithoutDraft - Returns only builder configlets
               IgnoreDraft - Returns everything other than draft configlets
               Static - Returns static configlets
               Generated - Returns generated configlets
               All - Returns all configlets

            Multiple values separated by comma can be given to type parameter
            (eg. static,generated will fetch both the types)."""
        URL = "/cvpservice/configlet/getConfiglets.do?"
        if cType == "All":  # Get a list of all configlets
            parameters = {"startIndex": 0, "endIndex": 0,
                         "sortByColumn": "name", "sortOrder": "Desc"}
        else:  # Get a list of all configlets of type - cType
            parameters = {"type": cType, "startIndex": 0, "endIndex": 0,
                         "sortByColumn": "name", "sortOrder": "Desc"}
        response = requests.get(self.url+URL, cookies=self.cookies, 
            params=parameters, verify=False)
        if "[404]" in response:
            text = "Error: %s configlets_get failed 404 error invalid URL" %self.host
            raise serverCvpError(text)
        elif "errorMessage" in str(response.json()):
            text = "Error: %s configlets_get failed - %s" %(self.host, response.json()[
                'errorMessage'])
            raise serverCvpError(text)
        else:
            return response.json()["data"]

    def configlet_check(self, name):
        """ 
            Check if configlet exists if not create it
            return config [config] and configlet key [key]
            return [new] as True if Configlet created
        """
        URL = "/cvpservice/configlet/getConfigletByName.do?name=%s" % name
        response = requests.get(self.url+URL, cookies=self.cookies, verify=False)
        if 'config' and 'key' in response.json():
            config = response.json()['config']
            key = response.json()['key']
            new = False
        elif "errorMessage" in str(response.json()):
            if "Entity does not exist" not in response.json()["errorMessage"]:
                text = "Error: %s configlet_check_find failed for %s - %s" % (self.host,name,response.json()['errorMessage'])
                raise serverCvpError(text)
            else:
                URL = "/cvpservice/configlet/addConfiglet.do"
                data = {'config': "", 'name': name}
                headers = {'Content-Type': 'application/json'}
                parameters = {}
                response = requests.post(self.url+URL, cookies=self.cookies,json=data, headers=headers, params=parameters, verify=False)
                if "errorMessage" in str(response.json()):
                    text = "Error: %s configlet_check_add failed for %s - %s" % (self.host,name,response.json()['errorMessage'])
                    raise serverCvpError(text)
                elif 'config' and 'key' in response.json()['data']:
                    config = response.json()['data']['config']
                    key = response.json()['data']['key']
                    new = True
                else:
                    return False
        return {'name':name, 'key': key, 'config': config, 'new': new}

    def configlet_update(self, name, config, key):
        """
            Update Configlet with name [name] and Configlet Key [key]
            with configuration in [config] string
            Update will overwrite existing config in Configlet
        """
        URL = '/cvpservice/configlet/updateConfiglet.do'
        data = {"config": config, "key": key, "name": name}
        headers = {'Content-Type': 'application/json'}
        parameters = {}
        response = requests.post(self.url+URL, cookies=self.cookies,
                                 json=data, headers=headers, params=parameters, verify=False)
        if "errorMessage" in str(response.json()):
            text = "Error: %s configlet_update failed - %s" %(self.host, response.json()[
                'errorMessage'])
            raise serverCvpError(text)
        return response    

def file_write(filePath, data, fileType, silent=True):
    """ filePath - full directory and filename for file
        Function returns True is file is successfully written
        data - content to write to file
        fileType
          json - JSON formatted text file
          text - Text file
        """
    directory, filename = os.path.split(filePath)
    try:
        os.makedirs(directory)
    except OSError:
        # directory already exists
        pass
    else:
        if not silent:
            print(f"Directory did not exist: Created - {directory}")

    if os.path.exists(filePath) and os.path.getsize(filePath) > 0:
        if not silent:
            print(f"Appending data to file: {filename}")
        fileOp = "a"
    else:
        if not silent:
            print(f"Creating file {filename}")
        fileOp = "w"
    try:
        with open(filePath, fileOp) as FH:
            if fileOp == "a":
                FH.seek(0, 2)
            if fileType.lower() == "json":
                json.dump(data, FH, sort_keys = True, indent = 4, ensure_ascii = True)
                result = True
            elif fileType.lower() == "text":
                FH.writelines(data)
                result = True
            else:
                if not silent:
                    print(f"Invalid fileType: {fileType}")
                result = False
    except IOError as file_error:
        if not silent:
            print(f"{filename} File Write Error: {file_error}")
        result = False
    return result

def main(server1, server2, cvp_user, cvp_pass, filter="all", overwrite=False, add=False):
    print ("\n\n###########  START  ########## \n")
    print ("  creating backup directories ")
    server1path = str(os.path.abspath(os.path.dirname(sys.argv[0])))+"/Backup_"+str(server1)+"/"
    server2path = str(os.path.abspath(os.path.dirname(sys.argv[0])))+"/Backup_"+str(server2)+"/"
    print(f"  Files will be saved to:\n   {server1path}\n   {server2path}")   
    print("\n\n######  Collecting Configlet Info  #####\n")
    print(f"  Connecting to {server1}")
    cvp1 = serverCvp(server1,cvp_user,cvp_pass)
    cvp1Auth = cvp1.logOn()
    print(f"  Checking permissions on {server1}")
    # Check for RW permissions to configlet and networkProvisioning on server1
    configletRW = False
    provisionRW = False
    for permission in cvp1Auth["permissionList"]:
        if permission["name"] == "configlet" and permission["mode"] == "rw":
            configletRW = True
        if permission["name"] == "networkProvisioning" and permission["mode"] == "rw":
            provisionRW = True
    if configletRW and provisionRW:
        print(f"  User permissions on {server1} are correct\n")
    else:
        print(f"  User needs RW permissions Configlet Management and Network Provisioning on {server1} ")
        raise SystemExit
    print(f"  Connecting to {server2}")
    cvp2 = serverCvp(server2,cvp_user,cvp_pass)
    cvp2Auth = cvp2.logOn()
    print(f"  Checking permissions on {server2}")
    # Check for RW permissions to configlet and networkProvisioning on server2
    configletRW = False
    provisionRW = False
    for permission in cvp2Auth["permissionList"]:
        if permission["name"] == "configlet" and permission["mode"] == "rw":
            configletRW = True
        if permission["name"] == "networkProvisioning" and permission["mode"] == "rw":
            provisionRW = True
    if configletRW and provisionRW:
        print(f"  User permissions on {server2} are correct")
    else:
        print(f"  User needs RW permissions Configlet Management and Network Provisioning on {server2} ")
        raise SystemExit
    # Collect Configlet details from CVP servers
    s1_configlets = cvp1.configlets_get(cType="Static")
    s2_configlets = cvp2.configlets_get(cType="Static")
    s1_targetConfiglets = []
    s2_targetConfiglets = []
    print("\n\n######  Scan and Backup Configlets  #####\n")
    with tqdm(total=len(s1_configlets)) as pbar:
            pbar.set_description("  Checking Configlets for %s" % server1)
            for configlet in s1_configlets:
                if filter in configlet["name"]:
                    configletFile = server1path+str(configlet["name"])+".json"
                    file_write(configletFile, configlet, "json")
                    s1_targetConfiglets.append(configlet)
                pbar.update(1)
    with tqdm(total=len(s2_configlets)) as pbar:
            pbar.set_description("  Checking Configlets for %s" % server2)
            for configlet in s2_configlets:
                if filter in configlet["name"]:
                    configletFile = server2path + str(configlet["name"])+".json"
                    file_write(configletFile, configlet, "json")
                    s2_targetConfiglets.append(configlet)
                pbar.update(1)
    print("\n\n######  Comparing Configlets  #####\n")
    with tqdm(total=len(s1_targetConfiglets)) as pbar1:
        pbar1.set_description("  Compare and Sync configlets")
        for s1configlet in s1_targetConfiglets:
            s2found = False
            for s2configlet in s2_targetConfiglets:
                if s1configlet["name"] == s2configlet["name"]:
                    s2found = True
                    # If there are matching configlets on both servers then sync or overwrite as required
                    if overwrite:
                        cvp2.configlet_update(s2configlet["name"], s1configlet["config"], s2configlet["key"])
                    else:
                        if s1configlet["dateTimeInLongFormat"] >= s2configlet["dateTimeInLongFormat"]:
                            cvp2.configlet_update(s2configlet["name"], s1configlet["config"], s2configlet["key"])
                        else:
                            cvp1.configlet_update(s1configlet["name"], s2configlet["config"], s1configlet["key"])
            if add and not s2found:
                # If there are not matching configlets on both servers then add configlet if required
                newConfiglet = cvp2.configlet_check(s1configlet["name"])
                if newConfiglet:
                    if newConfiglet["new"]:
                        # If a configlet was found then something went wrong with the match above so do nothing
                        cvp2.configlet_update(newConfiglet["name"], s1configlet["config"], newConfiglet["key"])
            pbar1.update(1)

    print("\n##########  END  ##########")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-s','--srcServer',required=True, type=str, help='Source CloudVision server, e.g 10.83.12.79')
    parser.add_argument('-d','--destServer',required=True, type=str, help='Destination CloudVision server, e.g 10.83.12.79')
    parser.add_argument('-u','--user', required=True, type=str, help='CloudVision User Name')
    parser.add_argument('-p','--passwd', required=True,type=str, help="User's Password")
    parser.add_argument('-f','--filter', required=False, type=str, help="Configlet Filter (lazy match)",default='all')
    parser.add_argument('-o', '--overwrite', required=False, help="Overwrite destServer configlets with srcServer", action='store_true')
    parser.add_argument('-a', '--add', required=False, help="Add missing configlets form srcServer to destServer", action='store_true')
    args = parser.parse_args()
    main(args.srcServer, args.destServer, args.user, args.passwd, args.filter, args.overwrite, args.add)
