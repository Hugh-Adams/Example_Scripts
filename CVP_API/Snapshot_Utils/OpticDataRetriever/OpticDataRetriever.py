#!/usr/bin/env python
#
# Copyright (c) 2019, Arista Networks, Inc.
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
# Locate PSM4 QSFPs from Snapshot for CVP 2018.1.x
#
#    Version 0.1 22/01/2019
# 
#    Written by:
#       Hugh Adams, Arista Networks
#
#    Revision history:
#       0.1 - 22/01/2019 - initial script
#
# Requires a user with read access to "Snapshots" in CVP
# Requires a snapshot to be created with the following commands
# show inventory | json
# show lldp neighbors | json
#
# Requires CVP user credentials
#

# Import Required Libraries
import json
import re
import os, csv
import argparse
import getpass
import sys
import json
import requests
from requests import packages
from time import sleep

# Global Variables

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


def fileOpen(filePath,fileType):
    """ filePath - full directory and filename for file
        function returns file contents based on selection
        json - JSON object
        txt - text string
        csv - Comma Separated Variable
        j2 - Jinja2 Template object"""
    if os.path.exists(filePath) and os.path.getsize(filePath) > 0:
        print "Retrieving file:%s" %filePath
        if fileType.lower() == "xl":
            fileObject = xlrd.open_workbook(filePath)
        else:
            with open(filePath, 'r') as FH:
                if fileType.lower() == "json":
                    fileObject = json.load(FH)  
                elif fileType.lower() == "txt":
                    fileObject = FH.readlines()
                elif fileType.lower() == "csv":
                    file_data = csv.reader(FH)
                    fileObject = output = list(file_data)
                elif fileType.lower() == "j2":
                    fileObject = Template(FH.read())
                else:
                    print "Invalid fileType"
                    fileObject = False
        return fileObject
    else:
        print "File does not exist or is empty: %s" %filePath
        return False

def fileWrite(filePath,data,fileType,option="c"):
    """ filePath - full directory and filename for file
        Function returns True is file is successfully written to media
        data - content to write to file
        fileType
          json - JSON object
          txt - text string
          csv - Comman Separated Variable string
        option
          a - append
          w - overwrite
          c - choose option based on file existance
        """
    if option.lower() == "c":
        if os.path.exists(filePath) and os.path.getsize(filePath) > 0:
            print "Appending data to file:%s" %filePath
            fileOp = "a"
        else:
            print "Creating file %s to write data to" %filePath
            fileOp = "w"
    else:
        fileOp = option.lower()
    try:
        with open(filePath, fileOp) as FH:
            if fileOp == "a":
                FH.seek(0, 2)
            if fileType.lower() == "json":
                #json.dump(json.loads(data), FH, sort_keys = True, indent = 4, ensure_ascii = True)
                json.dump(data, FH, sort_keys = True, indent = 4, ensure_ascii = True)
                result = True
            elif fileType.lower() == "txt":
                FH.writelines(data)
                result = True
            elif fileType.lower() == "csv":
                #write_csv = csv.writer(FH, dialect='excel')
                write_csv = csv.writer(FH)
                write_csv.writerows(data)
                result = True
            else:
                print "Invalid fileType"
                result = False
    except IOError as file_error:
        print "File Write Error: %s"%file_error
        result = False
    return result

def parseArgs():
    """Gathers comand line options for the script, generates help text and performs some error checking"""
    # Configure the option parser for CLI options to the script
    usage = "usage: %prog [options] userName password configlet xlfile"
    parser = argparse.ArgumentParser(description="Excel File to JSON Configlet Builder")
    parser.add_argument("--userName", help='Username to log into CVP')
    parser.add_argument("--password", help='Password for CVP user to login')
    parser.add_argument("--target", nargs="*", metavar='TARGET', default=[],
                        help='List of CVP appliances to get snapshot from URL,URL')
    parser.add_argument("--snapshot", help='CVP Snapshot containing Show Inventory and Show LLDP neighbor data')
    parser.add_argument("--opticType", default='PSM4', help="Optic Type to look for")
    parser.add_argument("--verbose", default=False, help='Return more information to the command line')
    args = parser.parse_args()
    return checkArgs( args )

def askPass( user, host ):
    """Simple function to get missing password if not recieved as a CLI option"""
    prompt = "Password for user {} on host {}: ".format( user, host )
    password = getpass.getpass( prompt )
    return password

def checkArgs( args ):
    """check the correctness of the input arguments"""
    # Set Intial Variables required
    getCvpAccess = False
    destList = []

    # React to the options provided  

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
             
    # CVP appliances to get snapsots from
    if not args.target:
        applianceNumber = int(raw_input("Number of CVP Appliance to use: "))
        loop = 0
        while loop < applianceNumber:
            args.target.append(raw_input("CVP Appliance %s: " %(loop+1)))
            loop += 1

    # Target snapshot
    if args.snapshot == None:
        args.snapshot = raw_input("Name of Snapshot to retrieve: ")
    else:
        if (args.snapshot[0] == args.snapshot[-1]) and args.snapshot.startswith(("'", '"')):
            args.snapshot = args.snapshot[1:-1]

    return args


# Main Script
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
                        if "lldp" in str(commandEntry).lower():
                            resultTable["lldp"]=commandEntry["response"]
                        if "inventory" in str(commandEntry).lower():
                            resultTable["inventory"]=commandEntry["response"]
                snapshotList[str(count)+"_"+snapshotDetails["hostname"]]=resultTable

            # Use Snapshot data to Create Optics report
            print "Snapshot retrieved: %s \n" % options.snapshot
            # deviceReport will be used to create the CSV ouput with the column headings as below
            deviceReport = [["ReortNumber","DeviceName","Interface","TransieverTYpe","SerialNumber",
                            "Neighbor","NeighborInterface"]]
            for deviceResults in snapshotList:
                # Work through inventory list and find optics
                print "looking at %s" %deviceResults
                inventory = json.loads(snapshotList[deviceResults]["inventory"])
                lldp = json.loads(snapshotList[deviceResults]["lldp"])
                hostname = re.split('_',str(deviceResults))[1]
                reportNumber = re.split('_',str(deviceResults))[0]
                for interface in inventory["xcvrSlots"]:
                    if options.opticType.lower() in inventory["xcvrSlots"][interface]["modelName"].lower():
                        xcvrList = []
                        interfaceName = "Ethernet"+str(interface)
                        print "Interface %s - Serial Number %s" %(interfaceName,inventory["xcvrSlots"][interface]["serialNum"])
                        xcvrList=[reportNumber,hostname,interfaceName,inventory["xcvrSlots"][interface]["modelName"],
                                  inventory["xcvrSlots"][interface]["serialNum"]]
                        # Work through list of interfaces with matching optics and find neighbors
                        print "Checking Neighbor Interfaces for %s ..." %interfaceName
                        for neighbor in lldp["lldpNeighbors"]:
                            print str(neighbor["port"])
                            if interfaceName in str(neighbor["port"]):
                                print "Found: %s-%s" %(neighbor["neighborDevice"],neighbor["neighborPort"])
                                xcvrList.append(neighbor["neighborDevice"])
                                xcvrList.append(neighbor["neighborPort"])
                        deviceReport.append(xcvrList)
            fullPath = os.path.abspath(os.path.dirname(sys.argv[0]))
            filePath = "%s/%s-%s.csv" %(fullPath,hostname,options.opticType)
            saveReport = fileWrite(filePath,deviceReport,"csv","w")
            if saveReport:
                print "Optics report saved to: %s" %filePath
        else:
            print "No Snapshots found"
        print "Logout from CVP:%s"% cvpSession.logOut()['data']
        print "Retrieved %s Snapshots from %s" %(totalSnapshots,cvpServer)

if __name__ == '__main__':
    main()
