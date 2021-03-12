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
# Audits Containers Configlets and Devices for CVP 2018.2.x
#
#    Version 0.2 22/03/2019
#
#    Written by:
#       Hugh Adams, Arista Networks
#
#    Revision history:
#       0.1 - 22/01/2019 - initial script
#       0.2 - 22/03/2019 - added Device Audit and reworked getting device to use provisioning tree
#
# Requires CVP user credentials
#
DOCUMENTATION = """
---
Script: CVPauditReport.py
version_added: "0.2"
supported CVP version: 2018.2.x
author: "Hugh Adams EMEA AS Team(ha@arista.com)"
short_description: Audit CVP Containers, Configlets, and Devices.
description:
  - CloudVison Portal Configlets, Containers, and Devices provide the means to
    build configurations for Arista devices managed by CVP.
  - The Audit Report provides concise CSV outputs that audit the structure of the
    configuration generated, along with associated Software Images applied and
    final device configurations. These reports provide a simple way to audit CVP
    instalations and compare multiple CVP instalations across different sites
  - Three reports can be produced:
      DeviceReport - CSV matrix of Devices and the configlets applied to them
      ConfigletReport - CSV matrix of Configlets, Configlet Type (Static, Builder)
                        Container Applied to, and devices affected by it
      Configlet Diffs - Comparison of similar configlets across multiple CVP instances,
                        used to check consistence of applied configuration. Report
                        includes a camparison score (100 - identical, 0 - very different)
                        and a separate diff file (html) highlighting the differences
      The reports will be saved to the same directory location as the script
options:
  username:
    description - CloudVision Portal user name to login with, if accessing multiple
                  instances of CVP the username must be available in each instance
    required - true
    default - null
  password:
    description - Password for user specified in username if accessing multiple
                  instances of CVP the password must be the same in each instance
    required - true
    default - null
  target:
    description - List of CVP appliances to create reports for, the primary node in
                  each cluster should be provided. Each URL or IP address separated
                  by a comma.
    required - true
    default - null
  configlet:
    description - List of name filters to use to match (include) configlets in
                  the audit report. Assuming a standard naming convention this list
                  can be used to filter out device specific configlets as these are
                  likely to different for each device making any diff report with
                  them in pointless.
    required - true
    default - null
  option:
    description - List of reports to create, each report option separated by a
                  comma.
    options - all - ouptut all avialable reports
            - configlet - output configlet assingments 1 report per CVP appliance
                          includes configlet associations and final device configurations
            - configuration - output comparison of simalar configlets across CVP appliances
            - devices - ouput of device inventory type data
    required - true
    default - null
  diffRatio:
    description - Comparison threshold used to decide if two configlets are similar
                  enough to be the same. A ratio of 100 would mean that both configlets
                  would have to be identical. A ratio of 90 generally gives a good
                  comaprison result.
    required - false
    default - 90
"""

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
import difflib
from fuzzywuzzy import fuzz # Library that uses Levenshtein Distance to calculate the differences between strings.

# Global Variables
auditOptions=["all","configlet","configuration","devices"]

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

    def getConfiglets(self, cType = "All"):
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
        getURL = "/cvpservice/configlet/getConfiglets.do?"
        if cType == "All": # Get a list of all configlets
            getParams = {"startIndex":0,"endIndex":0,"sortByColumn":"name","sortOrder":"Desc"}
        else: # Get a list of all configlets of type - cType
            getParams = {"type":cType,"startIndex":0,"endIndex":0,"sortByColumn":"name","sortOrder":"Desc"}
        response = requests.get(self.url+getURL,cookies=self.cookies,params=getParams,verify=False)
        if "[404]" in response:
            text = "Error gerConfiglets failed: 404 error invalid URL"
            raise serverCvpError(text)
        elif "errorMessage" in str(response.json()):
            text = "Error gerConfiglets failed: %s" % response.json()['errorMessage']
            raise serverCvpError(text)
        else:
            return response.json()

    def getConfigletDevices(self, name):
        """ Get a list of all devices associated with a named configlet
            name - name of configlet to look for."""
        getURL = "/cvpservice/configlet/getAppliedDevices.do?"
        getParams = {"configletName":name, "startIndex":0, "endIndex":0}
        response = requests.get(self.url+getURL,cookies=self.cookies,params=getParams,verify=False)
        if "[404]" in response:
            text = "Error getConfiglets failed: 404 error invalid URL"
            raise serverCvpError(text)
        elif "errorMessage" in str(response):
            text = "Error getConfigletDevices failed: %s" % response.json()['errorMessage']
            raise serverCvpError(text)
        return response.json()

    def getDevices(self):
        # Get All devices in the Inventory
        getURL = "/cvpservice/provisioning/searchTopology.do?"
        getParams = {"queryParam":".","startIndex":"0","endIndex":"0"}
        response = requests.get(self.url+getURL,cookies=self.cookies,params=getParams,verify=False)
        if "errorMessage" in str(response.json()):
            text = "Error Get Devices failed: %s" % response.json()['errorMessage']
            raise serverCvpError(text)
        return response.json()

    def getConfiguration(self, deviceKey):
        # Get Configuration for device with Key (systemMac)
        getURL = "/cvpservice/inventory/getInventoryConfiguration.do?"
        getParams = {"netElementId":deviceKey}
        response = requests.get(self.url+getURL,cookies=self.cookies,params=getParams,verify=False)
        if "errorMessage" in str(response.json()):
            text = "Error Get Configuration failed: %s" % response.json()['errorMessage']
            raise serverCvpError(text)
        return response.json()

    def getConfigletContainers(self, name):
        """ Get a list of all devices associated with a named configlet
            name - name of configlet to look for."""
        getURL = "/cvpservice/configlet/getAppliedContainers.do?"
        getParams = {"configletName":name, "startIndex":0, "endIndex":0}
        response = requests.get(self.url+getURL,cookies=self.cookies,params=getParams,verify=False)
        if "[404]" in response:
            text = "Error gerConfiglets failed: 404 error invalid URL"
            raise serverCvpError(text)
        elif "errorMessage" in str(response):
            text = "Error getConfigletContainers failed: %s" % response.json()['errorMessage']
            raise serverCvpError(text)
        return response.json()

def compare(fromText, toText, fromDesc, toDesc, lines=10):
    """ Compare text string in 'fromText' with 'toText' and produce
        diffRatio - a score as a float in the range [0, 1] 2.0*M / T
          T is the total number of elements in both sequences,
          M is the number of matches.
          Score - 1.0 if the sequences are identical, and 0.0 if they have nothing in common.
        unified diff list
          Code	Meaning
          '- '	line unique to sequence 1
          '+ '	line unique to sequence 2
          '  '	line common to both sequences
          '? '	line not present in either input sequence
        formatted HTML table to be written to a file
    """
    fromlines = fromText.splitlines(1)
    tolines = toText.splitlines(1)
    diffFile = difflib.HtmlDiff().make_file(fromlines, tolines,fromDesc,toDesc,context="-c", numlines=lines)
    diff = list(difflib.unified_diff(fromlines, tolines,n=lines))
    textComp = difflib.SequenceMatcher(None, fromText, toText)
    diffRatio = round( textComp.quick_ratio()*100, 2)
    return [diffRatio,diff,diffFile]

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
          csvList - list of row lists
          csvDict - list of row dictionaries,
                    first element of the list is a list of headers
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
    directory, filename = os.path.split(filePath)
    try:
        os.makedirs(directory)
    except OSError:
        # directory already exists
        pass
    else:
        print "Directory did not exist: Created - %s" %directory
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
            elif fileType == "csvList":
                write_csv = csv.writer(FH, dialect="excel")
                write_csv.writerows(data)
                result = True
            elif fileType == "csvDict":
                headers = data[0]
                write_csv = csv.DictWriter(FH, fieldnames=headers, dialect="excel")
                write_csv.writeheader()
                for row in data[1:]:
                    write_csv.writerow(row)
                result = True
            else:
                print "Invalid fileType: %s" %fileType
                result = False
    except IOError as file_error:
        print "%s File Write Error: %s"%(filename,file_error)
        result = False
    return result

def parseArgs(auditOptions):
    """Gathers comand line options for the script, generates help text and performs some error checking"""
    # Configure the option parser for CLI options to the script
    usage = "usage: %prog [options] username password target configlet option diffRatio"
    parser = argparse.ArgumentParser(description="CVP Audit Report Tool")
    parser.add_argument("--username", help='Username to log into CVP')
    parser.add_argument("--password", help='Password for CVP user to login')
    parser.add_argument("--target", help='List of CVP appliances to get reports for URL,URL')
    parser.add_argument("--configlet", help='List of configlet name filters for comaprison Audit')
    parser.add_argument("--option", help='Audit Options are %s'%auditOptions)
    parser.add_argument("--diffRatio", help="Configlet Name Comparision Ratio")
    args = parser.parse_args()
    return checkArgs( args,auditOptions )

def askPass( user, host ):
    """Simple function to get missing password if not recieved as a CLI option"""
    prompt = "Password for user {} on host {}: ".format( user, host )
    password = getpass.getpass( prompt )
    return password

def checkArgs( args,auditOptions ):
    """check the correctness of the input arguments"""
    # Set Intial Variables required
    getCvpAccess = False
    destList = []

    # React to the options provided

    # CVP Username for script to use
    if args.username == None:
        getCvpAccess = True

    # CVP Password for script to use
    if args.password == None:
        getCvpAccess = True
    else:
        if (args.password[0] == args.password[-1]) and args.password.startswith(("'", '"')):
            password = args.password[1:-1]

    if getCvpAccess:
        args.username = raw_input("User Name to Access CVP: ")
        args.password = askPass( args.username, "CVP" )

    # CVP appliances to Audit
    if not args.target:
        applianceNumber = int(raw_input("Number of CVP Appliance to use: "))
        loop = 0
        args.target=[]
        while loop < applianceNumber:
            args.target.append(raw_input("CVP Appliance %s: " %(loop+1)))
            loop += 1
    else:
        if (args.target[0] == args.target[-1]) and args.target.startswith(("'", '"')):
                    args.target = args.target[1:-1]
        targets = args.target
        if "," in targets:
            args.target = re.split(',',args.target)
        else:
            args.target = [targets] # Create a list of hosts instead of a text string

    # Configlet filters to use
    if not args.configlet:
        configletNumber = int(raw_input("Number of CVP configlet filters to create: "))
        if configletNumber == 0:
            args.configlet = "all"
        else:
            loop = 0
            args.configlet = []
            while loop < configletNumber:
                args.configlet.append(raw_input("CVP Configlet filter %s: " %(loop+1)))
                loop += 1
    else:
        if (args.configlet[0] == args.configlet[-1]) and args.configlet.startswith(("'", '"')):
                    args.configlet = args.configlet[1:-1]
        configlets = args.configlet
        if "," in configlets:
            args.configlet = re.split(',',args.configlet)
        else:
            args.configlet = [configlets] # Create a list of configlets instead of a text string

    # Options to use
    if not args.option:
        entryCorrect = False
        args.option = []
        while not entryCorrect:
            optionEntry = raw_input("Enter Required Audit Options %s (no spaces): " %auditOptions)
            if "," in optionEntry:
                optionEntry = re.split(',',optionEntry.lower())
            else:
                optionEntry = [optionEntry.lower()]
            for option in optionEntry:
                if option in auditOptions:
                    args.option.append(option)
                    entryCorrect = True
                else:
                    print "Please enter only %s" %auditOptions
                    entryCorrect = False
                    break
    else:
        if (args.option[0] == args.option[-1]) and args.option.startswith(("'", '"')):
                    args.option = args.option[1:-1]
        optionEntry = args.option
        if "," in optionEntry:
            optionEntry = re.split(',',args.option).lower()
        else:
            args.option = [optionEntry.lower()]

    # diffRatio
    if not args.diffRatio:
        args.diffRatio = 90
    else:
        args.diffRatio = int(args.diffRatio)

    return args


# Main Script
def main():
    # Get CLI Options
    options = parseArgs(auditOptions)
    fullPath = os.path.abspath(os.path.dirname(sys.argv[0]))

    # Get SnapShotData from CVP
    if any(option in options.option for option in ["all","configlet"]):
        print "Generating Configlet and Device Reports from CVP"
        for cvpServer in options.target:
            print "Attaching to API on %s to get Report Data" %cvpServer
            try:
                cvpSession = serverCvp(str(cvpServer),options.username,options.password)
                logOn = cvpSession.logOn()
            except serverCvpError as e:
                text = "serverCvp:(main1)-%s" % e.value
                print text
            print "Login Complete"
            configletDataList = cvpSession.getConfiglets()
            deviceListData = cvpSession.getDevices()
            print "\nGenerating Configlet Report for %s\n" %cvpServer
            # Create Report of Configlets vs Containers and Devices
            configletList = {}
            for configlet in configletDataList["data"]:
                configletList[str(configlet["name"])]={"type":str(configlet["type"])}
            for configlet in configletList:
                print "Found Configlet: %s" %configlet
                try:
                    configletDeviceData = cvpSession.getConfigletDevices(configlet)["data"]
                except KeyError:
                    # Skip Configlet as there is an issue with it
                    configletError = cvpSession.getConfigletDevices(configlet)
                    print "Problem with loading Configlet Device Data: %s" %configletError
                    if "errorCode" in str(configletError):
                        configletContainerList = [configletError["errorMessage"]]
                        configletDeviceList = [configletError["errorMessage"]]
                    else:
                        configletContainerList = ["error"]
                        configletDeviceList = ["error"]
                else:
                    configletDeviceList = []
                    for device in configletDeviceData:
                        print "   Matched Device %s" %device["hostName"]
                        configletDeviceList.append(device["hostName"])
                    configletContainerListData = cvpSession.getConfigletContainers(configlet)["data"]
                    configletContainerList = []
                    for container in configletContainerListData:
                        print "   Matched Container %s" %container["containerName"]
                        configletContainerList.append(container["containerName"])
                configletList[configlet]["devices"]= configletDeviceList
                configletList[configlet]["containers"]= configletContainerList
            configletReport = [["configletName","configletType","containersApplied","devicesApplied"]]
            for configlet in sorted(list(configletList)):
                containerString = "\r".join(str(item) for item in sorted(configletList[configlet]["containers"]) )
                deviceString = "\r".join(str(item) for item in sorted(configletList[configlet]["devices"]))
                configletReport.append({"configletName":str(configlet),"configletType":configletList[configlet]["type"],"containersApplied":containerString,
                                        "devicesApplied":deviceString})
            #fullPath = os.path.abspath(os.path.dirname(sys.argv[0]))
            filePath = "%s/%s-ConfigletReport.csv" %(fullPath,cvpServer)
            saveReport = fileWrite(filePath,configletReport,"csvDict","w")
            if saveReport:
                print "Configlet report saved to: %s" %filePath
            # Create a report Devices vs Configlets
            print "\nGenerating Device Report\n"
            deviceReportData = {}
            deviceReportHeaders = ["name"]
            deviceReportHeaders.extend(sorted(list(configletList)))
            deviceReportHeaders.append("RunningConfig")
            deviceReport =[deviceReportHeaders]
            for device in deviceListData["netElementList"]:
                print "Found Device: %s" %device["fqdn"]
                deviceReportData[str(device["fqdn"])]={"name":str(device["fqdn"]),"RunningConfig":cvpSession.getConfiguration(device["systemMacAddress"])["output"]}
            for configletName in configletList:
                print "Found Configlet: %s" %configletName
                appliedDevices = cvpSession.getConfigletDevices(str(configletName))
                if "errorCode" in str(appliedDevices):
                    print "Problem with Configlet %s: %s" %(configletName,appliedDevices["errorMessage"])
                else:
                    for device in appliedDevices["data"]:
                        print "   Matched Device: %s" %device["hostName"]
                        deviceReportData[str(device["hostName"])][str(configletName)]="yes"
            for device in deviceReportData:
                filePath = "%s/Configs/%s-DeviceConfig.txt" %(fullPath,str(device))
                saveConfig = fileWrite(filePath,deviceReportData[device]["RunningConfig"],"txt","w")
                if saveConfig:
                    print "Device Running Config saved to: %s" %filePath
                    deviceReportData[device]["RunningConfig"] = filePath
                else:
                    deviceReportData[device]["RunningConfig"] = "None"
                deviceReport.append(deviceReportData[device])
            filePath = "%s/%s-DeviceReport.csv" %(fullPath,cvpServer)
            saveReport = fileWrite(filePath,deviceReport,"csvDict","w")
            if saveReport:
                print "Device report saved to: %s" %filePath
            print "\nLogout from %s: %s"% (cvpServer,cvpSession.logOut()['data'])
            print "\nCompleted Reports for %s" %(cvpServer)
    if any(option in options.option for option in ["all","configuration"]):
        # Create Reports for similar configlets in each CVP instance
        # login into all CVP instances then compare similar configlets
        # make sure there are at least to CVP targets to compare assume target 1 is the prime instance
        if len(options.target) > 1:
            cvpObjects = []
            print "Generating Configlet and Device Reports from CVP"
            for cvpServer in options.target:
                print "Attaching to API on %s to get Configlet Delta Report Data" %cvpServer
                try:
                    cvpSession = serverCvp(str(cvpServer),options.username,options.password)
                    logOn = cvpSession.logOn()
                except serverCvpError as e:
                    text = "serverCvp:(main1)-%s" % e.value
                    print text
                print "Logged into %s" %cvpServer
                cvpObjects.append({"hostName":cvpServer,"server":cvpSession,"configlets":[]})
            # Get a list of configlets from CVP servers
            for index, session in enumerate(cvpObjects):
                staticConfiglets = session["server"].getConfiglets("Static")["data"]
                for configlet in staticConfiglets:
                    # Only compare configlets if they match required configlet name filters
                    if any("all" in configletFilter.lower() for configletFilter in options.configlet):
                        cvpObjects[index]["configlets"].append({"name":configlet["name"],"config":configlet["config"]})
                    else:
                        if any(configletFilter.lower() in configlet["name"].lower() for configletFilter in options.configlet):
                            cvpObjects[index]["configlets"].append({"name":configlet["name"],"config":configlet["config"]})
            # Compare config in CVP server 1 with their counterparts in the otherCVP servers
            configReport = [["hostname_1","configletName_1","diffScore","hostname_2","configletName_2","diff_File"]]
            for count,cvpObject in enumerate(cvpObjects[1:]): # Miss out first instance as that is the comparision object
                print "%s Checking %s" %(str(count+1),cvpObject["hostName"])
                for refConfiglet in cvpObjects[0]["configlets"]:
                    for compConfiglet in cvpObject["configlets"]:
                        if fuzz.ratio(compConfiglet["name"],refConfiglet["name"]) > options.diffRatio:
                            # compare(fromText, toText, fromDesc, toDesc, lines=10)
                            fromDesc = str(re.split('\.',cvpObjects[0]["hostName"])[0])+'-'+str(refConfiglet["name"])
                            toDesc = str(re.split('\.',cvpObject["hostName"])[0])+'-'+str(compConfiglet["name"])
                            configDiff = compare(refConfiglet["config"], compConfiglet["config"],fromDesc,toDesc)
                            # returned contains configDiff[diffRatio,diff,diffFile]
                            diffReportName = "%s/%s-%s_ConfigDiff_Report.html" %(fullPath,str(count+1),fromDesc+'-WITH-'+toDesc)
                            diffReport = fileWrite(diffReportName,configDiff[2],"txt","w")
                            if diffReport:
                                print "Config Diff report saved to: %s" %diffReportName
                            configReport.append({"hostname_1":cvpObject["hostName"],"configletName_1":compConfiglet["name"],
                                                 "diffScore":configDiff[0],"hostname_2":cvpObjects[0]["hostName"],
                                                 "configletName_2":refConfiglet["name"],"diff_File":diffReportName})
            # Save comparison scores to csv file.
            reportPath = "%s/ConfigDiffs_Report.csv" %(fullPath)
            saveReport = fileWrite(reportPath,configReport,"csvDict","w")
            if saveReport:
                print "CVP Configlet Config Diffs report saved to: %s" %reportPath
            # Logout of all CVP Servers
            for cvpSession in cvpObjects:
                print "Logout from %s: %s"% (cvpServer,cvpSession["server"].logOut()['data'])
    if any(option in options.option for option in ["all","devices"]):
        # Create Reports for Devices in Containers each CVP instance
        print "Generating Device Reports from CVP"
        for cvpServer in options.target:
            print "Attaching to API on %s to get Configlet Delta Report Data" %cvpServer
            try:
                cvpSession = serverCvp(str(cvpServer),options.username,options.password)
                logOn = cvpSession.logOn()
            except serverCvpError as e:
                text = "serverCvp:(main1)-%s" % e.value
                print text
            print "Logged into %s" %cvpServer
            devices = cvpSession.getDevices()
            if devices["total"] > 0:
                deviceList = devices["netElementList"]
                deviceReport = [["Line","hostname","IPaddress","systemMacAddress","serialNumber","Container","SWversion"]]
                for count,device in enumerate(deviceList):
                    deviceReport.append({"Line":count+1,"hostname":device["fqdn"],"IPaddress":device["ipAddress"],
                                         "systemMacAddress":device["systemMacAddress"],"serialNumber":device["serialNumber"],
                                         "Container":device["containerName"],"SWversion":device["version"]})
                deviceReportName = "%s/%s-Device_Report.csv" %(fullPath,cvpServer)
                saveReport = fileWrite(deviceReportName,deviceReport,"csvDict","w")
                if saveReport:
                    print "Device report saved to: %s" %deviceReportName
            else:
                print "No Devices found in %s\n" %cvpServer
        # Logout of CVP Server
        print "Logout from %s: %s"% (cvpServer,cvpSession.logOut()['data'])
    if not any(option in options.option for option in auditOptions):
        print "Invalid Report Option Requested %s Valid Options are %s" %(options.option,auditOptions)
    print "\nAll Reports Completed and Saved to %s" %fullPath

if __name__ == '__main__':
    main()
