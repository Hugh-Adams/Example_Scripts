#!/usr/bin/env python3
#
# Copyright (c) 2018, Arista Networks, Inc.
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
# IF NOT ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Snapshot Transfer for CVP 
#
#    Version 0.4 25/01/2021
# 
#    Written by:
#       Hugh Adams, Arista Networks
#
#    Revision history:
#       0.1 - initially script
#       0.2 - added command line arguments
#       0.3 - updated for CVP 2018.2
#       0.4 - updated to Python 3
#       
# Requires a user with read access to CVP Provisioning GUI
#
import argparse
import getpass
import os, sys
import json
import requests
from requests import packages
from datetime import datetime

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

    def __init__ (self,HOST,USER,PASS):
        self.url = "https://%s"%HOST
        self.authenticateData = {'userId' : USER, 'password' : PASS}
        requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:ECDH+3DES:DH+3DES:RSA+AESGCM:RSA+AES:RSA+3DES:!aNULL:!MD5:!DSS'
        from requests.packages.urllib3.exceptions import InsecureRequestWarning
        try:
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        except packages.urllib3.exceptions.ProtocolError as e:
            if str(e) == "('Connection aborted.', gaierror(8, 'nodename nor servname provided, or not known'))":
                raise serverCvpError("DNS Error: The CVP Server %s can not be found" % HOST)
            elif str(e) == "('Connection aborted.', error(54, 'Connection reset by peer'))":
                raise serverCvpError( "Error, connection aborted")
            else:
                raise serverCvpError("Could not connect to Server")

    def logOn(self):
        try:
            headers = { 'Content-Type': 'application/json' }
            loginURL = "/web/login/authenticate.do"
            response = requests.post(self.url+loginURL,json=self.authenticateData,headers=headers,verify=False)
            if "errorMessage" in str(response.json()):
                text = "Error log on failed: %s" % response.json()['errorMessage']
                raise serverCvpError(text)
        except requests.HTTPError as e:
            raise serverCvpError("Error HTTP session to CVP Server: %s" % str(e))
        except requests.exceptions.ConnectionError as e:
            raise serverCvpError("Error connecting to CVP Server: %s" % str(e))
        except:
            raise serverCvpError("Error in session to CVP Server")
        self.cookies = response.cookies
        return response.json()

    def logOut(self):
        headers = { 'Content-Type':'application/json' }
        logoutURL = "/cvpservice/login/logout.do"
        response = requests.post(self.url+logoutURL, cookies=self.cookies, json=self.authenticateData,headers=headers,verify=False)
        return response.json()
    
    def getTemplateKeyofSnapshot(self, name):
        # Get the templatekey for the specific Snapshot name
        getURL = "/cvpservice/snapshot/templates?"
        getParams = {"queryparam":name,"startIndex":0, "endIndex":0}
        response = requests.get(self.url+getURL,cookies=self.cookies,params=getParams,verify=False)
        if "errorMessage" in str(response.json()):
            text = "Error gerSnapshot data failed: %s" % response.json()['errorMessage']
            raise serverCvpError(text)
        templateKey = response.json()["templateKeys"][0]["key"]
        return templateKey      

    def getDeviceListSnapshotData(self, key):
        # Get the device list in Serialnumbers for the specific Snapshot Template ID
        getURL = "/cvpservice/snapshot/template?"
        getParams = {"templateId":key}
        response = requests.get(self.url+getURL,cookies=self.cookies,params=getParams,verify=False)
        if "errorMessage" in str(response.json()):
            text = "Error getSnapshot data failed: %s" % response.json()['errorMessage']
            raise serverCvpError(text)
        return response.json()["deviceList"]

    def getDeviceHostName(self):
        # Get the device hostnames for the serialNumbers
        getURL = "/cvpservice/inventory/devices?"
        getParams = {"provisioned":"false"}
        response = requests.get(self.url+getURL,cookies=self.cookies,params=getParams,verify=False)
        if "errorMessage" in str(response.json()):
            text = "Error getSnapshot data failed: %s" % response.json()['errorMessage']
            raise serverCvpError(text)
        return response.json()
        
    def getSnapshotFromTelemetry(self, deviceId, snapshotId):
        # Get the Result data for Snapshot
        getURL = "/api/v1/rest/cvp/snapshots/status/"+deviceId+"/snapshots/ids/"+snapshotId
        response = requests.get(self.url+getURL,cookies=self.cookies,verify=False)
        if "errorMessage" in str(response.json()):
            text = "Error getSnapshot data failed: %s" % response.json()['errorMessage']
            raise serverCvpError(text)
        return response.json()["notifications"][0]["updates"]
                  
        
def main(options):
    print("\n\n###########  START  ########## \n")
    options.destPath = str(os.path.abspath(os.path.dirname(sys.argv[0])))+"/snapshots/"
    print(f"Files will be saved to: {options.destPath}\n")

    # Get SnapShotData from CVP
    print("Retrieving SnapShot from CVP")
    for cvpServer in options.server:
        print(f"Attaching to API on {cvpServer} to get Snapshot Data")
        try:
            cvpSession = serverCvp(str(cvpServer),options.user,options.passwd)
            logOn = cvpSession.logOn()
        except serverCvpError as e:
            text = "serverCvp:(main1)-%s" % e.value
            print(text)
        print("Login Complete")
        snapshotTemplateKey = cvpSession.getTemplateKeyofSnapshot(options.snapshot)
        deviceListSnapshot = cvpSession.getDeviceListSnapshotData(snapshotTemplateKey)
        deviceListHostname = cvpSession.getDeviceHostName()
        deviceSerialPair = {}
        i = 0
        for key in deviceListHostname:
            deviceSerialPair[deviceListHostname[i]["serialNumber"]] = deviceListHostname[i]["hostname"]
            i +=1
        snapshotData = {}
        snapshotDataFiltered = {}
        for device in deviceListSnapshot:
            snapshotData[device] = cvpSession.getSnapshotFromTelemetry(device,snapshotTemplateKey)
            command_index = 0
            for key in snapshotData[device][snapshotTemplateKey]["value"]["Output"]:
                command = snapshotData[device][snapshotTemplateKey]["value"]["Output"][command_index]["Command"]
                resultkey = snapshotData[device][snapshotTemplateKey]["value"]["Output"][command_index]["Result"]
                if command_index == 0:
                    snapshotDataFiltered[device]= {command:snapshotData[device][resultkey+"_0"]["value"]}
                else:
                    snapshotDataFiltered[device].update({command:snapshotData[device][resultkey+"_0"]["value"]})
                command_index += 1
        
        print(f"Snapshot data obtained for {len(snapshotDataFiltered)} Devices")
        print(f"Snapshot retrieved: {options.snapshot} \n")
        # Save Results data to files in text and json formats

        for deviceResults in snapshotDataFiltered:
            for command in snapshotDataFiltered[deviceResults]:
                snapshotTextFile = options.destPath+str(deviceSerialPair[deviceResults])+"_"+str(command)+"_"+datetime.fromtimestamp(snapshotData[deviceResults]["ExecutionTime"]["value"]//1000000000).strftime("%Y_%m_%d %H_%M_%S")+".txt"
                snapshotJsonFile = options.destPath+str(deviceSerialPair[deviceResults])+"_"+str(command)+"_"+datetime.fromtimestamp(snapshotData[deviceResults]["ExecutionTime"]["value"]//1000000000).strftime("%Y_%m_%d %H_%M_%S")+".json"
                try:
                    fhandle = open(snapshotTextFile, 'w')
                except IOError as file_error:
                    file_error_text = str("File Open Error:"+str(file_error))
                    print(file_error_text)
               
                fhandle.write(str(command)+"\n"+str(snapshotDataFiltered[deviceResults][command]))
                fhandle.write("\n")
                print (f"Snapshot Text for {str(deviceResults)} in file: {snapshotTextFile}")
                fhandle.close()
                try:
                    fhandle = open(snapshotJsonFile, 'w')
                except IOError as file_error:
                    file_error_text = str("File Open Error:"+str(file_error))
                    print(file_error_text)
                json.dump(snapshotDataFiltered[deviceResults][command],fhandle, sort_keys = True, indent = 4, ensure_ascii = True)
                print(f"Snapshot JSON Data for {str(deviceResults)} in file: {snapshotJsonFile}")
                fhandle.close()

        print(f"Logout from CVP:{cvpSession.logOut()['data']}")

if __name__ == '__main__':
    #Gather comand line options for the script
    usage = "usage: %prog [options] userName passwd server destPath snapshot"
    parser = argparse.ArgumentParser(description="Fetch Snapshots from CVP")
    parser.add_argument("--user",required=True, help='Username to log into CVP')
    parser.add_argument("--passwd", help='passwd for CVP user to login')
    parser.add_argument("--server", nargs="*", metavar='server', default=[],
                        help='List of CVP appliances to get snapshot from URL,URL')
    parser.add_argument("--snapshot", default=None, help='Name of snapshot to retrieve')                                      
    args = parser.parse_args()
    
    #check the correctness of the input arguments
    # Set Intial Variables required
    getCvpAccess = False
    destList = []

    # React to the options provided  
    # Directory to copy Snapshot files to

    # CVP Username for script to use
    if args.user == None:
        getCvpAccess = True
        
    # CVP Password for script to use
    if args.passwd == None:
        getCvpAccess = True
    else:
        if (args.passwd[0] == args.passwd[-1]) and args.passwd.startswith(("'", '"')):
            passwd = args.passwd[1:-1]

    if getCvpAccess:
        args.user = input("User Name to Access CVP: ")
        # Get missing password if not received as a CLI option
        prompt = "Password for user %s on CVP: " %args.user
        args.passwd = getpass.getpass( prompt )
             
    # CVP appliances to get Snapshots from
    if not args.server:
        applianceNumber = int(input("Number of CVP Appliance to use: "))
        loop = 0
        while loop < applianceNumber:
            args.server.append(input("CVP Appliance %s: " %(loop+1)))
            loop += 1

    # server snapshot
    if args.snapshot == None:
        args.snapshot = input("Name of Snapshot to retrieve: ")
    else:
        if (args.snapshot[0] == args.snapshot[-1]) and args.snapshot.startswith(("'", '"')):
            args.snapshot = args.snapshot[1:-1]
    main(args)
