#!/usr/bin/env python
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
#    Version 0.2 10/02/2018
# 
#    Written by:
#       Hugh Adams, Arista Networks
#
#    Revision history:
#       0.1 - initially script
#       0.2 - added command line arguments
#       
# Requires a user "backup" with access to files created on CVP
#
import argparse
import getpass
import sys
import json
import requests
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

    def __init__ (self,HOST,USER,PASS):
        self.url = "https://%s"%HOST
        self.authenticateData = {'userId' : USER, 'password' : PASS}
        requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:ECDH+3DES:DH+3DES:RSA+AESGCM:RSA+AES:RSA+3DES:!aNULL:!MD5:!DSS'
        from requests.packages.urllib3.exceptions import InsecureRequestWarning
        try:
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        except packages.urllib3.exceptions.ProtocolError as e:
            if str(e) == "('Connection aborted.', gaierror(8, 'nodename nor servname provided, or not known'))":
                raise serverCvpError("DNS Error: The CVP Server %s can not be found" % CVPSERVER)
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

    def getNamedSnapshot(self, name):
        # Get the Template Key for the Snapshot in question
        getURL = "/cvpservice/snapshot/getSnapshots.do?"
        getParams = {"queryparam":name,"startIndex":0, "endIndex":0}
        response = requests.get(self.url+getURL,cookies=self.cookies,params=getParams,verify=False)
        if "errorMessage" in str(response.json()):
            text = "Error gerSnapshot details failed: %s" % response.json()['errorMessage']
            raise serverCvpError(text)
        templateKeyList = []
        for element in response.json()["data"]:
            templateKey = element["templateKey"]
            if not (templateKey in templateKeyList):
                templateKeyList.append(templateKey)
        # Get Snapshots using that template
        responseData = {"total":0, "data":[]}
        for tKey in templateKeyList:
            getURL = "/cvpservice/snapshot/getSnapshotsByTemplateId.do"
            getParams = {"templateKey":tKey,"startIndex":0, "endIndex":0}
            response = requests.get(self.url+getURL,cookies=self.cookies,params=getParams,verify=False)
            if "errorMessage" in str(response.json()):
                text = "Error gerSnapshot details failed: %s" % response.json()['errorMessage']
                raise serverCvpError(text)
            else:
                responseData["total"]+= response.json()["total"]
                responseData["data"]+= response.json()["data"]
        return responseData
    
    def getSnapshotData(self, key):
        # Get the Result data for Snapshot
        getURL = "/cvpservice/snapshot/getSnapshotById.do?"
        getParams = {"snapshotId":key}
        response = requests.get(self.url+getURL,cookies=self.cookies,params=getParams,verify=False)
        if "errorMessage" in str(response.json()):
            text = "Error gerSnapshot data failed: %s" % response.json()['errorMessage']
            raise serverCvpError(text)
        return response.json()

def parseArgs():
    """Gathers comand line options for the script, generates help text and performs some error checking"""
    usage = "usage: %prog [options] userName password target destPath snapshot"
    parser = argparse.ArgumentParser(description="Fetch Snapshots from CVP")
    parser.add_argument("--userName",required=True, help='Username to log into CVP')
    parser.add_argument("--password", help='Password for CVP user to login')
    parser.add_argument("--target", nargs="*", metavar='TARGET', default=[],
                        help='List of CVP appliances to get snapshot from URL,URL')
    parser.add_argument("--destPath",default=None, help='Directory to copy Snapshots to')
    parser.add_argument("--snapshot", default=None, help='Name of snapshot to retrieve')                                      
    args = parser.parse_args()
    return checkArgs( args )

def askPass( user, host ):
    """Simple function to get missing password if not recieved as a CLI option"""
    prompt = "Password for user {} on host {}: ".format( user, host )
    password = getpass.getpass( prompt )
    return password

def checkArgs( args ):
    '''check the correctness of the input arguments'''
    # Set Intial Variables required
    getCvpAccess = False
    destList = []

    # React to the options provided  
    # Directory to copy Snapshot files to
    if args.destPath == None:
        args.destPath = raw_input("Destination Backup Directory Path: ")

    # CVP Username for script to use
    if args.userName == None:
        getCvpAccess = True
        
    # CVP Password for script to use
    if args.password == None:
        getCvpAccess = True
    else:
        if (args.password[0] == args.password[-1]) and args.password.startswith(("'", '"')):
            password = args.password[1:-1]

    if getCvpAccess:
        args.userName = raw_input("User Name to Access CVP: ")
        args.password = askPass( args.userName, "CVP" )
             
    # CVP appliances to get Snapshots from
    if not args.target:
        applianceNumber = int(raw_input("Number of CVP Appliance to use: "))
        loop = 0
        while loop < applianceNumber:
            args.target.append(raw_input("CVP Appliance %s: " %(loop+1)))
            loop += 1

    # Target container for snapshot
    if args.snapshot == None:
        args.snapshot = raw_input("Name of Snapshot to retrieve: ")
    else:
        if (args.snapshot[0] == args.snapshot[-1]) and args.snapshot.startswith(("'", '"')):
            args.snapshot = args.snapshot[1:-1]

    return args


def main():
    # Get CLI Options
    options = parseArgs()

    # Get SnapShotData from CVP
    print "Retrieving SnapShot from CVP"
    for cvpServer in options.target:
        print "Attaching to API on %s to get Snapshot Data" %cvpServer
        try:
            cvpSession = serverCvp(str(cvpServer),options.userName,options.password)
            logOn = cvpSession.logOn()
        except serverCvpError as e:
            text = "serverCvp:(main1)-%s" % e.value
            print text
        print "Login Complete"
        snapshotInfo = cvpSession.getNamedSnapshot(options.snapshot)
        snapshotData = snapshotInfo['data']
        totalSnapshots = snapshotInfo['total']
        snapshotList = {}
        print "Snapshot List obtained for %s Snapshots" %totalSnapshots
        if len(snapshotData) > 0:
            for count, snapshotDetails in enumerate (snapshotData):
                resultTable = {}
                snapshotResponse = cvpSession.getSnapshotData(snapshotDetails["key"])
                snapshotResult = snapshotResponse["custom_command_data"]["data"]
                snapshotTemplate = snapshotResponse["templateName"]
                for commandEntry in snapshotResult:
                    if not "failureCount" in commandEntry:
                        resultTable[str(commandEntry["command"])]=commandEntry["response"]
                snapshotList[str(count)+"_"+snapshotDetails["hostname"]+"_"+snapshotTemplate]=resultTable

            # Save Results data to files in text and json formats
            print "Snapshot retrieved: %s \n" % options.snapshot
            for deviceResults in snapshotList:
                snapshotTextFile = options.destPath+str(deviceResults)+".txt"
                snapshotJsonFile = options.destPath+str(deviceResults)+".json"
                try:
                    fhandle = open(snapshotTextFile, 'w')
                except IOError as file_error:
                    file_error_text = str("File Open:"+str(file_spec)+"Error:"+str(file_error))
                    print file_error_text
                # Write out test data to text file 
                for entry in snapshotList[deviceResults]:
                    test = str(entry)+"\n"+str(snapshotList[deviceResults][entry])
                    fhandle.write(test)
                    fhandle.write("\n")
                print "Snapshot Text for %s in file: %s" % (str(deviceResults),snapshotTextFile)
                fhandle.close()
                try:
                    fhandle = open(snapshotJsonFile, 'w')
                except IOError as file_error:
                    file_error_text = str("File Open:"+str(file_spec)+"Error:"+str(file_error))
                    print file_error_text
                json.dump(snapshotList[deviceResults],fhandle, sort_keys = True, indent = 4, ensure_ascii = True)
                print "Snapshot JSON Data for %s in file: %s" % (str(deviceResults),snapshotJsonFile)
                fhandle.close()

        else:
            print "No Snapshots found"

        print "Logout from CVP:%s"% cvpSession.logOut()['data']
        print "Retrieved %s Snapshots from %s" %(totalSnapshots,cvpServer)

if __name__ == '__main__':
    main()
