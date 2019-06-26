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
# Excel File to Data Configlet Import for CVP 2018.1.x
#
#    Version 0.5 13/02/2019
# 
#    Written by:
#       Hugh Adams, Arista Networks
#
#    Revision history:
#       0.1 - 21/11/2018 - initial script
#       0.2 - 26/11/2018 - excel data stored in a per Configlet format
#       0.3 - 20/12/2018 - import existing JSON to ammend
#       0.4 - 01/02/2019 - import existing CVP JSON configlet
#       0.5 - 13/02/2019 - create mlag ID for Multi Chassis Port Channels
#
# Requires a user with write access to "Configlets" in CVP
# Requires a location of the Excel file, the Data Configlet Name, and CVP user credentials
#

# Import Required Libraries

import xlrd
import xlwt
from netaddr import *
import json
import re
from collections import OrderedDict
import os
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

    def listConfiglet(self):
        getURL = "/cvpservice/configlet/getConfiglets.do?"
        getParams = {'startIndex':0,'endIndex':0,'type':'Configlet'}
        response = requests.get(self.url+getURL,cookies=self.cookies,params=getParams,verify=False)
        if "errorMessage" in str(response.json()):
            text = "(class-serverCvp-listConfiglet)-Error List Configlets failed: %s" % response.json()['errorMessage']
            raise serverCvpError(text)
        return response.json()

    def getConfiglet(self, name):
        getConfigletURL = "/cvpservice/configlet/getConfigletByName.do?"
        getConfigletParams = {'name':name}
        response = requests.get(self.url+getConfigletURL,cookies=self.cookies,params=getConfigletParams,verify=False)
        if "errorMessage" in str(response.json()):
            text = "(class-serverCvp-getConfiglet)-Error Configlet get failed: %s" % response.json()['errorMessage']
            raise serverCvpError(text)
        return response.json()

    def addNoteConfiglet (self,deviceKey, note="Generated By Script"):
        headers = { 'Content-Type': 'application/json'}
        updateParams = {}
        updateURL = "/cvpservice/configlet/addNoteToConfiglet.do"
        updateData = {"key":deviceKey, "note":note}
        response = requests.post(self.url+updateURL,cookies=self.cookies,json=updateData,headers=headers,params=updateParams, verify=False)
        if "errorMessage" in str(response.json()):
            text = "(class-serverCvp-addNoteConfiglet)-Error Configlet update Note: %s" % response.json()['errorMessage']
            raise serverCvpError(text)
        return response.json()

    def updateConfiglet (self, configletName, deviceKey, deviceConfig, note="Generated By Script"):
        headers = { 'Content-Type': 'application/json'}
        updateParams = {}
        updateURL = "/cvpservice/configlet/updateConfiglet.do"
        updateData = {"config":deviceConfig, "key":deviceKey, "name":configletName}
        response = requests.post(self.url+updateURL,cookies=self.cookies,json=updateData,headers=headers,params=updateParams, verify=False)
        if "errorMessage" in str(response.json()):
            text = "(class-serverCvp-updateConfiglet)-Error Configlet update failed: %s" % response.json()['errorMessage']
            raise serverCvpError(text)
        return response.json()

    def newConfiglet (self, configletName, deviceConfig, note="Generated By Script"):
        headers = { 'Content-Type': 'application/json'}
        postParams = {}
        postURL = "/cvpservice/configlet/addConfiglet.do"
        postData = {"config":deviceConfig, "name":configletName}
        response = requests.post(self.url+postURL,cookies=self.cookies,json=postData,headers=headers,params=postParams, verify=False)
        if "errorMessage" in str(response.json()):
            text = "(class-serverCvp-newConfiglet)-Error Configlet creation failed: %s" % response.json()['errorMessage']
            raise serverCvpError(text)
        return response.json()
    
def fileOpen(filePath,fileType):
    """ filePath - full directory and filename for file
        function returns file contents based on selection
        json - JSON object
        txt - text string
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
                elif fileType.lower() == "j2":
                    fileObject = Template(FH.read())
                else:
                    print "Invalid fileType"
                    fileObject = False
        return fileObject
    else:
        print "File does not exist or is empty: %s" %filePath
        return False

def asnCalc(asn):
    """ calculate both types of ASN plain and dotted fron ASN value
        if the ASN has a dot in it assume as-asdot otherwise as-asplain
        return both types asn-asdot followed by asn-asplain"""
    if "." in str(asn):
        asnSplit= re.split('\.',str(asn))
        asdot=str(asn)
        asplain = str((int(asnSplit[0])*65536)+int(asnSplit[1]))
    else:
        asDot_Top = str(int(float(asn)//65536))
        asDot_Btm = str(int(float(asn)%65536))
        asDot_Btm = asDot_Btm.rjust(5, '0')
        asdot = asDot_Top+"."+asDot_Btm
        asplain = str(asn)
    return [asdot,asplain]


def xlconvertJSON(workBook, jsonObject={}, sheetName="all", testing=False):
    """ sheetName used to specify a single sheet to convert
        otherwise default is all sheets
        workBook is excel workbook object returned by xlrd.open"""
    # Function Variables
    # none
    if sheetName == "all":
        sheetList = workBook.sheet_names()
    elif sheetName in str(workBook.sheet_names()):
        sheetList = [sheetName]
    else:
        print "Sheet %s Not Found" %sheetName
        return False
    print "Sheets to convert: %s" %sheetList
    
    # jsonObject={} JSON object to store excel data in, created by default as function parameter
    deviceList={} # key:hostname list for reference when adding device data to objects
    
    # Work through each Tab in Spreadsheet, base config tab creates switch data object
    # additional tabs then add configuration data to each switch object.

    for sheet_name in sheetList:
        print "Converting sheet: %s" %sheet_name
        target_sheet = workBook.sheet_by_name(sheet_name)
        # Get Column headings
        try:
            sheetKeys = [v.value.lower() for v in target_sheet.row(0)]
            variableKeys = [v.value for v in target_sheet.row(0)]
        except IndexError:
            if testing:
                print "Not converting sheet %s: has no headings or is blank (indexError)" %sheet_name
        else:
            # If a set of heading is generated then work through sheet otherwise move onto next sheet
            # GLOBAL Tab is required to build script/configuration variables from.
            if "global" in sheet_name.lower():
                print "Generating Script Variables from %s" %sheet_name
                try:
                    jsonObject["siteConstants"]
                except KeyError:
                    jsonObject["siteConstants"]={}
                for row in range(target_sheet.nrows):
                    varName = str(target_sheet.cell(row, 0).value).replace(' ', '')
                    if "," in str(target_sheet.cell(row, 1).value):
                        jsonObject["siteConstants"][varName]=re.split(",",str(target_sheet.cell(row, 1).value))
                    else:
                        jsonObject["siteConstants"][varName]=str(target_sheet.cell(row, 1).value)
            # Assuming some global variable names to generate script variables
            # Get MLAG settings and correctly format them if necessary
                # MLAG peer VLAN
                if "." in str(jsonObject["siteConstants"]["MLAGpeer"]):
                    mlagVLAN = re.split("\.",str(jsonObject["siteConstants"]["MLAGpeer"]))[0]        
                elif "vlan" in str(jsonObject["siteConstants"]["MLAGpeer"]).lower():
                    mlagVLAN = re.split("vlan",str(jsonObject["siteConstants"]["MLAGpeer"]).lower())[1]
                else:
                    mlagVLAN = jsonObject["siteConstants"]["MLAGpeer"]
                jsonObject["siteConstants"]["MLAGpeer"] = "vlan"+str(mlagVLAN)
                # MLAG Domain ID
                if "." in str(jsonObject["siteConstants"]["MLAGDomain"]):
                    mlagDomain = re.split("\.",str(jsonObject["siteConstants"]["MLAGDomain"]))[0]
                    jsonObject["siteConstants"]["MLAGDomain"]=mlagDomain
                else:
                    mlagDomain = jsonObject["siteConstants"]["MLAGDomain"]
            # Provide both ASdot and ASplain values for any BGP ASNs
                for entry in jsonObject["siteConstants"]:
                    if testing:
                        print "Checking: %s" %entry
                    if "asn" in str(entry).lower():
                        for count,asn in enumerate(jsonObject["siteConstants"][entry]):
                            jsonObject["siteConstants"][entry][count]=asnCalc(asn)
            
            # BASECONFIG Tab is required to build switch object types other sheets are optional.
            elif "baseconfig" in sheet_name.lower():
                print "Generating Device Objects from %s" %sheet_name
                # Need to find ASN can't assume it been found already
                asnIndex = 0
                for count, heading in enumerate(sheetKeys):
                    if str(heading) == "asn":
                        asnIndex=count
                for row in range(target_sheet.nrows):
                    if testing:
                        print "sheet: %s row: %s" %(sheet_name,row+1)
                    # Ignore 1st row as this has headings in
                    if row == 0:
                        continue
                    # Ignore rows without an entry in column a
                    elif target_sheet.cell_type(row,0) == xlrd.XL_CELL_EMPTY:
                        continue
                    # Create switch object data from columns that don't have do not use as a heading
                    # Keeping things simple make all keys lower case
                    else:
                        rowData = target_sheet.row(row)
                        for columnNumber, cell in enumerate(rowData):
                            if columnNumber == 0:
                                key=str(cell.value).lower()
                                try:
                                    jsonObject[key]
                                except KeyError:
                                    jsonObject[key]={}
                                    # baseconfig data is associated with "nw" configlet
                                    jsonObject[key]={"base":{},"vrfs":{},"nw":{"interface":{"Ethernet":{},"vlan":{},"portChannel":{},"loopback":{}},
                                                           "vlan":{},"mlag":{},"bgp":{"vrfs":{}}}}
                            elif "name" in sheetKeys[columnNumber]:
                                # Map system mac to device name for future reference in script
                                deviceList[str(cell.value)]=key
                                # Calculate Spanning Tree Priority
                                deviceFields = re.split('-',str(cell.value))
                                # Calculate Spanning Tree Priority base on Device Type (See Network Config Standards)
                                deviceType = deviceFields[2]+'-'+deviceFields[3]
                                if deviceType in jsonObject["siteConstants"]["lowLeafType"]:
                                    jsonObject[key]["base"]["STPpriority"] = "4096"
                                elif deviceType in jsonObject["siteConstants"]["highLeafType"]:
                                    jsonObject[key]["base"]["STPpriority"] = "32768"
                                else:
                                    jsonObject[key]["base"]["STPpriority"] = "49152"
                                # Calculate Virtual MAC base on Device Number (See Network Config Standards)
                                deviceNumber =int(deviceFields[-1])
                                # Create areaNumber either from vMACid in the Global Tab or the PoP designator else
                                # failing that set it to "00"
                                if "vMACid" in list(jsonObject["siteConstants"]):
                                    areaNumber = int(float(jsonObject["siteConstants"]["vMACid"]))
                                elif re.split(r"(\d+)", deviceFields[1])[1].isdigit():
                                    areaNumber=int(re.split(r"(\d+)", deviceFields[1])[1])
                                else:
                                    areaNumber = int(0)
                                if deviceNumber % 2 == 0:
                                  virtualMAC = "00:1C:73:ee:%02d:%02d" %(areaNumber,int(re.split('0x',hex(deviceNumber-1))[1]))
                                else:
                                  virtualMAC = "00:1C:73:ee:%02d:%02d" %(areaNumber,int(re.split('0x',hex(deviceNumber))[1]))
                                jsonObject[key]["base"]["virtualMAC"]=virtualMAC
                                # After working out various other values add name field to Device                                              
                                jsonObject[key]["base"][str(variableKeys[columnNumber]).replace(' ', '')] = str(cell.value)
                            # Extract the required VRF/Configlet objects to be created for the Device Object
                            elif "vrf" == str(sheetKeys[columnNumber]) and "vrf asn" == str(sheetKeys[columnNumber+1]):
                                if target_sheet.cell_type(row,columnNumber) != xlrd.XL_CELL_EMPTY:
                                    vrfList = re.split(",",cell.value)
                                    asnList = re.split(",",str(target_sheet.cell_value(row,columnNumber+1)))
                                    if len(vrfList) == len(asnList):
                                        # Work through vrfList to create each vrf entry then add ASN
                                        for vrf, asn in zip(vrfList, asnList):
                                            # Calculate ASN values and add them to the VRFs
                                            asnSplit=asnCalc(asn)
                                            jsonObject[key]["vrfs"][vrf]={"asn_asdot":asnSplit[0],"asn_asplain":asnSplit[1]}
                                            print "sheet %s row %s - creating [%s][vrfs][%s]" %(sheet_name,row+1,key,vrf)
                                    else:
                                        print "sheet %s row %s - VRF list does not match VRF ASN list" %(sheet_name,row+1)
                            # Skip the VRF ASN column as it was used previously and does not provide useful data on its own
                            elif "vrf asn" == str(sheetKeys[columnNumber]) and "vrf" == str(sheetKeys[columnNumber-1]):
                                continue
                            elif not("do not use" in sheetKeys[columnNumber]):
                                # If the cell has the BGP ASN in add it to "nw bgp" section
                                if "asn" == str(sheetKeys[columnNumber]):
                                    # If the cell is blank/empty don't work out the ASN
                                    if str(cell.value) != "":
                                        # Calculate ASN values
                                        asn = str(cell.value)
                                        asnSplit= asnCalc(asn)
                                        # Add them to bgp vrf default config for use in templates
                                        try:
                                            jsonObject[key]["nw"]["bgp"]["vrfs"]["default"]
                                        except KeyError:
                                            jsonObject[key]["nw"]["bgp"]["vrfs"]["default"]={"peer":{},"asn_asdot":asnSplit[0],"asn_asplain":asnSplit[1]}
                                        else:
                                            jsonObject[key]["nw"]["bgp"]["vrfs"]["default"]["asn_asdot"]=asnSplit[0]
                                            jsonObject[key]["nw"]["bgp"]["vrfs"]["default"]["asn_asplain"]=asnSplit[1]
                                        # Add them to vrfs for use later in script
                                        try:
                                            jsonObject[key]["vrfs"]["default"]
                                        except KeyError:
                                            jsonObject[key]["vrfs"]["default"]={"asn_asdot":asnSplit[0],"asn_asplain":asnSplit[1]}
                                        else:
                                            jsonObject[key]["vrfs"]["default"]["asn_asdot"]=asnSplit[0]
                                            jsonObject[key]["vrfs"]["default"]["asn_asplain"]=asnSplit[1]
                                # Find Management Gateway from mgmt IP, GW first IP in subnet
                                elif "mgmt ip" in sheetKeys[columnNumber]:
                                    ip = IPNetwork(str(cell.value))
                                    jsonObject[key]["base"]["mgmtGW"]=str(ip[1])
                                    jsonObject[key]["base"][str(variableKeys[columnNumber]).replace(' ', '')] = str(cell.value)
                                elif "loopback1"  == str(sheetKeys[columnNumber]):
                                    # If the cell is blank/empty don't add the Loopback or BGP data
                                    if str(cell.value) != "" or target_sheet.cell_type(row,columnNumber) != xlrd.XL_CELL_EMPTY:
                                        interface = 1
                                        asn = str(rowData[asnIndex].value)
                                        if testing:
                                            print "sheet %s row %s Adding LoopBack%s" %(sheet_name, row+1,interface)
                                        jsonObject[key]["nw"]["interface"]["loopback"][interface]={"type":"ROUTED",
                                                                                                   "description":"RouterID_%s"%asn,
                                                                                                   "ipAddr":str(cell.value),
                                                                                                   "mask":"/32",
                                                                                                   "vrf":"default"}
                                        # Check if vrfs default created if not create it
                                        try:
                                            jsonObject[key]["nw"]["bgp"]["vrfs"]["default"]
                                        except KeyError:
                                            jsonObject[key]["nw"]["bgp"]["vrfs"]["default"]={}
                                        jsonObject[key]["nw"]["bgp"]["vrfs"]["default"]["routerID"] = str(cell.value)
                                        try:
                                            jsonObject[key]["vrfs"]["default"]
                                        except KeyError:
                                            jsonObject[key]["vrfs"]["default"]={}
                                        jsonObject[key]["vrfs"]["default"]["routerID"] = str(cell.value)
                                else:
                                    jsonObject[key]["base"][str(variableKeys[columnNumber]).replace(' ', '')] = str(cell.value)
            # Other tabs add configuration data to device data from baseconfig
            # To add data it must be associated with a device, column "A" must be the device name - according to its heading
            # Data organised as Interface, VLAN, Portchannel, MLAG, BGP all with associated Configlet
            elif "device" in sheetKeys[0]:
                for row in range(target_sheet.nrows):
                    # If a device name does not match a SystemMAC:Hostname tuple then skip the device config
                    key = False
                    intType = False
                    if testing:
                        print "sheet: %s row: %s" %(sheet_name,row+1)
                    rowData = {}
                    # Ignore 1st row as this has headings in
                    if row == 0:
                        continue
                    # Ignore rows without an entry in column a
                    elif target_sheet.cell_type(row,0) == xlrd.XL_CELL_EMPTY:
                        if testing:
                            print "sheet: %s row: %s Device Name Missing or Empty"  %(sheet_name,row+1)
                        continue
                    # Ignore rows without an entry in column a
                    elif target_sheet.cell_type(row,1) == xlrd.XL_CELL_EMPTY:
                        if testing:
                            print "sheet: %s row: %s  Configlet Name Missing or Empty" %(sheet_name,row+1)
                        continue
                    # Create switch object data from columns that don't have "do not use" as a heading
                    # Keeping things simple make all keys lower case
                    # collect data then sort into data collections
                    else:
                        for columnNumber, cell in enumerate(target_sheet.row(row)):
                            # Check that the device object was created from baseconfig sheet
                            if columnNumber == 0:
                                try:
                                    key=deviceList[str(cell.value)]
                                    device=str(cell.value)
                                except KeyError:
                                    print "sheet %s row %s Device Not Found" %(sheet_name, row+1)
                                    key = False
                            # Check for errors in the cell
                            if cell.ctype > 0 and cell.ctype < 5:
                                # Only use spreadsheet cells that are not used for calculations
                                if not("do not use" in sheetKeys[columnNumber]):
                                    if str(cell.value) == "":
                                        rowData[sheetKeys[columnNumber]] = False
                                    else:
                                        rowData[sheetKeys[columnNumber]] = str(cell.value)
                            else:
                                if testing:
                                    if cell.ctype == 0:
                                        error = "Cell Empty 0"
                                    elif cell.ctype == 5:
                                        error = "error_text_from_cell %s" %cell.value
                                    elif cell.ctype == 6:
                                        error = "Cell Empty 6"
                                    else:
                                        error = "Unkown Cell Error: $s"%cell.ctype
                                    if not("do not use" in sheetKeys[columnNumber]):
                                        print "sheet %s row: %s Cell_Error %s-%s" %(sheet_name,row+1, sheetKeys[columnNumber],error)
                                rowData[sheetKeys[columnNumber]] = False
                        # rowData keys are assumed here, change to match spreadsheet
                        # If a valid key was found then add data otherwise skip it
                        if key:
                            # Data in row has a configlet associated with it, create configlet object
                            # if it has not been created before.
                            try:
                                configlet = rowData['configlet'].lower()
                                # See if the configlet data exists
                                configletData=jsonObject[key][configlet]
                            except KeyError:
                                # Create new configlet in data object
                                jsonObject[key][configlet]={}
                                # Create some data type in new configlet object
                                if testing:
                                    print "sheet: %s row: %s Creating JSON Data for %s" %(sheet_name,row+1,rowData['configlet'])
                                jsonObject[key][configlet]={"interface":{"Ethernet":{},"vlan":{},"portChannel":{},"loopback":{}},
                                                       "vlan":{},"mlag":{},"bgp":{}}
                                # Create data configlet object to add new row data to
                                configletData=jsonObject[key][configlet]
                            # Get VRF Membership for Interface
                            if testing:
                                print "sheet: %s row: %s Found vrf: %s" %(sheet_name,row+1,rowData["vrf"])
                            if rowData["vrf"]:
                                vrf = rowData["vrf"]
                            else:
                                vrf = "default"
                            if rowData["bgp peer ip"]:
                                # Create the VRF in BGP if not already there
                                try:
                                    jsonObject[key][configlet]["bgp"]["vrfs"]
                                except KeyError:
                                    jsonObject[key][configlet]["bgp"]["vrfs"]={}
                                try:
                                    jsonObject[key][configlet]["bgp"]["vrfs"][vrf]
                                except KeyError:
                                    #jsonObject[key][configlet]["bgp"]["vrfs"][vrf]={"peer":{}}
                                    jsonObject[key][configlet]["bgp"]["vrfs"][vrf]={}
                                if testing:
                                    print "sheet: %s row: %s vrf set to: %s" %(sheet_name,row+1,vrf)
                                
                            # Get a sorted list of VLANs if row has VLAN data
                            # "vlan" will have been set to False if there is no config
                            if rowData["vlan"]:
                                vlanList = []
                                if ',' in str(rowData["vlan"]):
                                    vlans = re.split(',',rowData["vlan"])
                                else:
                                    vlans=[rowData["vlan"]]
                                if testing:
                                    print "sheet: %s row: %s VLANs found:- %s" %(sheet_name,row+1,vlans)
                                # Handle Excel changing VLAN ID into a floating point number
                                for vl in vlans:
                                    if '.' in vl:
                                        vlanList.append(re.split('\.',vl)[0])
                                    else:
                                        vlanList.append(vl)
                                vlan = sorted(vlanList)
                                # Auto Correct interface type to ACCESS Trunk if there are more than 1 VLANs associated with it
                                if len(vlan) > 1:
                                    intType = "TRUNK"
                                else:
                                    intType = rowData["type"]
                                if testing:
                                    print "sheet: %s row: %s Interface: %s VLAN List Len: %s Type: %s" %(sheet_name,row+1,rowData["int"],len(vlan),intType)
                            else:
                                vlan = []
                                intType = rowData["type"]
                            # Get Port Channel Data
                            # "po" will have been set to False if there is no config
                            if rowData["po"]:
                                if "Po" in rowData["po"]:
                                    pchannel=re.split("Po",rowData["po"])[1]
                            else:
                                pchannel="no"
                            # Get Interface Data
                            # "int" will have been set to False if there is no config
                            if rowData["int"]:
                                if "eth" in rowData["int"].lower():
                                    interface = re.split("eth",rowData["int"].lower())[1]
                                    if testing:
                                        print "sheet %s row %s Adding %s-Ethernet%s" %(sheet_name,row+1,device,interface)
                                    # Need to check for existing VLANs on interface
                                    try:
                                        existVLANs = configletData["interface"]["Ethernet"][interface]["vlan"]
                                    except KeyError:
                                        addVLANs = vlan
                                    else:
                                        print "Addiong Eth VLANs %s to %s" %(vlan,existVLANs)
                                        if len(vlan) > 0 or len(existVLANs) >0:
                                            addVLANs = sorted(vlan.extend + existVLANs)
                                        else:
                                            addVLANs = vlan
                                    configletData["interface"]["Ethernet"][interface]={"type":intType,
                                                                                       "description":rowData["int desc"],
                                                                                       "ipAddr":rowData["ip address"],
                                                                                       "mask":rowData["mask"],
                                                                                       "vlan":addVLANs,
                                                                                       "portChannel":pchannel,
                                                                                       "vrf":vrf}
                                if "vlan" in rowData["int"].lower():
                                    interface = re.split("vlan",rowData["int"].lower())[1]
                                    if rowData["type"] == "ROUTED":
                                        if "_" in str(rowData["int desc"]):
                                            # removed +"_PTP" from end of following line
                                            vlanDesc = re.split('_',rowData["int desc"])[0]+"_"+vrf
                                        else:
                                            # removed +"_PTP" from end of following line
                                            vlanDesc = str(rowData["int"])+"_"+vrf
                                    else:
                                        vlanDesc = rowData["int desc"]+"_"+vrf+"_"+configlet
                                    if testing:
                                        print "sheet: %s row: %s Adding %s-VLAN%s" %(sheet_name,row+1,device,interface)
                                    configletData["interface"]["vlan"][interface]={"type":rowData["type"],
                                                                                   "description":rowData["int desc"],
                                                                                   "vlanDesc":vlanDesc,
                                                                                   "ipAddr":rowData["ip address"],
                                                                                   "mask":rowData["mask"],
                                                                                   "vrf":vrf}
                                    if interface == mlagVLAN:
                                        configletData["mlag"]["localIP"] = rowData["ip address"]
                                        configletData["mlag"]["peerIP"] = rowData["bgp peer ip"]
                                        configletData["mlag"]["domainID"] = mlagDomain
                                        
                                if "po" in rowData["int"].lower():
                                    interface = re.split("po",rowData["int"].lower())[1]
                                    if testing:
                                        print "sheet %s row %s Adding %s-PortChannel%s" %(sheet_name,row+1,device,interface)
                                    for vl in vlan:
                                        if str(vl) == mlagVLAN:
                                            PoInt = "Port-Channel%s" %interface
                                            if testing:
                                                print "sheet: %s row: %s Found MLAG peerlink - %s" %(sheet_name,row+1,PoInt)
                                            try:
                                                # Try to add new mlag peerlink key to "nw' mlag data
                                                jsonObject[key]["nw"]["mlag"]["peerLink"]=PoInt
                                            except KeyError:
                                                # Create new configlet mlag data object
                                                jsonObject[key]["nw"]={"mlag":{"peerLink":PoInt}}
                                    # Need to check for existing VLANs on interface
                                    try:
                                        existVLANs = configletData["interface"]["portChannel"][interface]["vlan"]
                                    except KeyError:
                                        addVLANs = vlan
                                    else:
                                        print "Addiong PO VLANs %s to %s" %(vlan,existVLANs)
                                        if len(vlan) > 0 or len(existVLANs) >0:
                                            addVLANs = sorted(vlan + existVLANs)
                                        else:
                                            addVLANs = vlan
                                    configletData["interface"]["portChannel"][interface]={"type":intType,
                                                                                          "description":rowData["int desc"],
                                                                                          "ipAddr":rowData["ip address"],
                                                                                          "mask":rowData["mask"],
                                                                                          "vlan":addVLANs,
                                                                                          "portChannel":pchannel,
                                                                                          "vrf":vrf}
                                    if "m_po" in rowData["int"].lower():
                                        configletData["interface"]["portChannel"][interface]["mlagID"]=interface
                                    else:
                                        configletData["interface"]["portChannel"][interface]["mlagID"]=False
                                        
                                if "lo" in rowData["int"].lower():
                                    interface = re.split("lo",rowData["int"].lower())[1]
                                    asn = re.split("_",rowData['int desc'])[1]
                                    if "." in asn:
                                        asnSplit = asnCalc(asn)
                                    else:
                                        print "sheet %s row %s %s is not a Valid ASN type" %(sheet_name,row+1,asn)
                                        asnSplit = [False,False]
                                    if testing:
                                        print "sheet %s row %s Adding %s-LoopBack%s" %(sheet_name,row+1,device,interface)
                                    configletData["interface"]["loopback"][interface]={"type":rowData["type"],
                                                                                       "description":rowData["int desc"],
                                                                                       "ipAddr":rowData["ip address"],
                                                                                       "mask":rowData["mask"],
                                                                                       "vrf":vrf}
                                    # Check to see if any peers have been created before.
                                    # Add VRF BGP Info and add VRF routerID to device VRFs data
                                    try:
                                        configletData["bgp"]["vrfs"][vrf]
                                    except KeyError:
                                        configletData["bgp"]["vrfs"][vrf]={"asn_asdot":asnSplit[0],"asn_asplain":asnSplit[1],
                                                               "routerID":rowData["ip address"]}
                                    else:
                                        configletData["bgp"]["vrfs"][vrf]["asn_asdot"]=asnSplit[0]
                                        configletData["bgp"]["vrfs"][vrf]["asn_asplain"]=asnSplit[1]
                                        configletData["bgp"]["vrfs"][vrf]["routerID"]=rowData["ip address"]
                                        if testing:
                                            print "sheet %s row %s - updating [%s][vrfs][%s][routerID][%s]" %(sheet_name,row+1,key,vrf,rowData["ip address"])
                                            try:
                                                jsonObject[key]["vrfs"][vrf]
                                            except KeyError:
                                                jsonObject[key]["vrfs"][vrf]={"asn_asdot":asnSplit[0],"asn_asplain":asnSplit[1],
                                                                              "routerID":rowData["ip address"]}
                                                print "sheet %s row %s - NOT FOUND [%s][vrfs][%s]" %(sheet_name,row+1,key,vrf)
                                            else:
                                                jsonObject[key]["vrfs"][vrf]["routerID"]=rowData["ip address"]
                                        
                            if testing:
                                print "sheet %s row %s BGP ASN: %s" %(sheet_name,row+1,rowData['bgp peer asn'])
                                print "sheet %s row %s BGP VRF %s" %(sheet_name,row+1,vrf)
                            # Get BGP Data
                            # "bgp peer asn" will have been set to False if there is no bgp config
                            if rowData["bgp peer asn"]:
                                peerASN = str(rowData["bgp peer asn"])
                                # Look for the vrf ASN if it can't be found then use the default vrf ASN
                                try:
                                    localASN = jsonObject[key]["vrfs"][vrf]["asn_asdot"]
                                except KeyError:
                                    localASN = jsonObject[key]["vrfs"]["default"]["asn_asdot"]
                                if peerASN == localASN:
                                    peerBGP = "local"
                                else:
                                    peerBGP = "remote"
                                if testing:
                                    print "sheet %s row %s Adding %s BGP ASN - %s IP - %s" %(sheet_name,row+1,device,peerASN,rowData["bgp peer ip"])
                                # Check to see if any peers have been created before.
                                try:
                                    configletData["bgp"]["vrfs"][vrf]["peer"]
                                except KeyError:
                                    configletData["bgp"]["vrfs"][vrf]["peer"]={}
                                if "_" in str(rowData["int desc"]):
                                    peerDesc = re.split('_',rowData["int desc"])[0]
                                else:
                                    peerDesc = str(rowData["int"])
                                configletData["bgp"]["vrfs"][vrf]["peer"][rowData["bgp peer ip"]]={"peerASN":peerASN,
                                                                               "peerVRF":rowData["vrf"],
                                                                               "peerBGP":peerBGP,
                                                                               "peerDesc":peerDesc,
                                                                               "routeMap_IN":rowData["route-map in"],
                                                                               "routeMap_OUT":rowData["route-map out"]}
                            # Update Configlet Data in Device object
                            jsonObject[key][configlet]=configletData
            else:
                if testing:
                    print "Not converting sheet %s: device not found in heading column A" %sheet_name

    return json.dumps(jsonObject)
                      
def parseArgs():
    """Gathers comand line options for the script, generates help text and performs some error checking"""
    # Configure the option parser for CLI options to the script
    usage = "usage: %prog [options] userName password configlet xlfile"
    parser = argparse.ArgumentParser(description="Excel File to JSON Configlet Builder")
    parser.add_argument("--userName", help='Username to log into CVP')
    parser.add_argument("--password", help='Password for CVP user to login')
    parser.add_argument("--target", help='CVP appliance to create Data Configlet on')
    parser.add_argument("--configlet", help='CVP Configlet to contain data')
    parser.add_argument("--overwrite", default='N', help="Overwrite Data configlet if it exists")
    parser.add_argument("--xlfile", help='Excel file (.xls) containing data')
    parser.add_argument("--jsonfile", default = False, help='Existing file (.json) containing JSON data from spreadsheet')
    parser.add_argument("--test", default='N',help='Testing do not use CVP')
    parser.add_argument("--verbose", default="N", help='Enable Verbose Output')
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
    # Excel file to get source data from
    if args.xlfile == None:
        args.xlfile = raw_input("Sorce Excel file path path and filename: ")

    # Ignore CVP options if testing
    if "n" in args.test.lower():
        args.test = False
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
                 
        # CVP appliances to get upload data to
        if args.target == None:
            args.target=raw_input("CVP Appliance URL/IP: ")

        # Target container for data
        if args.configlet == None:
            args.configlet = raw_input("Name of Data Configlet: ")
        else:
            if (args.configlet[0] == args.configlet[-1]) and args.configlet.startswith(("'", '"')):
                args.configlet = args.configlet[1:-1]
    else:
        args.test = True
        
    if "n" in args.verbose.lower():
        args.verbose = False
    else:
        args.verbose = True

    return args


# Main Script
def main():
    # Set Intial Variables required
    options = parseArgs()
    dataReady = False
    if options.verbose:
        print "Verbose Mode"
    if options.test:
        print "Testing - CVP Data Configlets will not be Created"

    #Open Excel Spreadsheet and get data object
    print "Reading Excel File"
    xlworkBook = fileOpen(options.xlfile, "xl")
    if xlworkBook:
        
        # Create path for use when writing files 
        pathString = os.path.split(os.path.realpath(options.xlfile))[0]+"/"

        # Open JSON file if specified and create JSON data object
        if options.jsonfile:
            if options.jsonfile.lower() == "cvp":
                # Create file path for saving Data to
                fileName = re.split('\.', os.path.split(options.xlfile)[1], 1, flags=re.IGNORECASE)[0]+".json"
                dataFile = pathString+fileName
                print "Retreiving JSON Data Configlet"
                #Attach to CVP instance
                print "Connecting to %s " %options.target
                try:
                    cvpSession = serverCvp(str(options.target),options.userName,options.password)
                    logOn = cvpSession.logOn()
                except serverCvpError as e:
                    print"   Connnection to %s:%s" %(options.target,e.value)
                
                #Check for existance of Data configlet
                getConfiglets = cvpSession.listConfiglet()['data']
                foundConfiglet = False
                for configlet in getConfiglets:
                    # print configlet['name']
                    if options.configlet == configlet['name']:
                        targetConfiglet = cvpSession.getConfiglet(configlet['name'])
                        print "Configlet %s found" %options.configlet
                        jsonObject = json.loads(cvpSession.getConfiglet(options.configlet)['config'])
                        foundConfiglet = True
                        dataReady = True
                #Close CVP instance
                cvpSession.logOut
                if foundConfiglet:
                    print "JSON data loaded"
                else:
                    print "No JSON Data loaded blank JSON object created"
                    jsonObject = {}
                    dataReady = True
            else:
                print "Reading JSON Data File"
                jsonObject = fileOpen(options.jsonfile, "json")
                if jsonObject:
                    # Create file path for saving Data to
                    JSONpath = os.path.split(os.path.realpath(options.jsonfile))[0]+"/"
                    fileName = re.split('\.', os.path.split(options.jsonfile)[1], 1, flags=re.IGNORECASE)[0]+".json"
                    dataFile = pathString+fileName
                    dataReady = True
        else:
            print "No JSON Data file specified creating new file:"
            # Create file path for saving Data to
            fileName = re.split('\.', os.path.split(options.xlfile)[1], 1, flags=re.IGNORECASE)[0]+".json"
            dataFile = pathString+fileName
            print "   %s" %dataFile
            jsonObject = {}
            dataReady = True

        if dataReady:
            #Convert Excel worksheets into JSON objects
            print "Converting Excel File to JSON data"
            # xlconvertJSON(workBook, sheetName="all", siteList, testing=False)
            cvpJSONdata = xlconvertJSON(xlworkBook, jsonObject,"all", options.verbose)

            # Skip using CVP while testing
            if not options.test:
                #Attach to CVP instance
                print "Connecting to %s " %options.target
                try:
                    cvpSession = serverCvp(str(options.target),options.userName,options.password)
                    logOn = cvpSession.logOn()
                except serverCvpError as e:
                    print"   Connnection to %s:%s" %(options.target,e.value)
                
                #Check for existance of Data configlet
                getConfiglets = cvpSession.listConfiglet()['data']
                foundConfiglet = False
                for configlet in getConfiglets:
                    print configlet['name']
                    if options.configlet == configlet['name']:
                        foundConfiglet = True
                        targetConfiglet = cvpSession.getConfiglet(configlet['name'])
                        print "Configlet %s found" %options.configlet
                #Confirm overwrite
                        question = True
                        changeConfiglet = False
                        while question:
                            changeQuestion = raw_input("    Do you want to overwrite the existing configlet:  %s (y/n): "%options.configlet)
                            if changeQuestion in "yYnN":
                                if changeQuestion in "yY":
                                    changeConfiglet = True
                                    question = False
                                else:
                                    changeConfiglet = False
                                    question = False
                            else:
                                print "Please Enter 'y' or 'n'"
                                question = True
                #print "configlet found: %s" %foundConfiglet
                #print "Configlet Change: %s" %configletChange

                # Update CVP with new Data as selected

                configletNote = "From file: %s" %options.xlfile

                if foundConfiglet:
                    if changeConfiglet:
                        configletKey = targetConfiglet["key"]
                        configletName = targetConfiglet["name"]
                        configletUpdate = cvpSession.updateConfiglet(configletName, configletKey, cvpJSONdata)
                        print "Configlet Overwritten: %s" %configletUpdate
                    else:
                        print "%s Unchanged" %targetConfiglet["name"]
                else:
                    question = True
                    createConfiglet = False
                    while question:
                        changeQuestion = raw_input("    Do you want to create a new configlet:  %s (y/n): "%options.configlet)
                        if changeQuestion in "yYnN":
                            if changeQuestion in "yY":
                                createConfiglet = True
                                question = False
                            else:
                                createConfiglet = False
                                question = False
                        else:
                            print "Please Enter 'y' or 'n'"
                            question = True
                    if createConfiglet:
                        newConfiglet = cvpSession.newConfiglet(options.configlet, cvpJSONdata, configletNote)
                        print "%s Created: %s" %(options.configlet, newConfiglet)
                        

                #Close CVP instance
                cvpSession.logOut

            # Option to write JSON data to File
            question = True
            createFile = False
            while question:
                fileQuestion = raw_input("    Do you want to create a new JSON data file:  %s (y/n): "%dataFile)
                if fileQuestion in "yYnN":
                    if fileQuestion in "yY":
                        createFile = True
                        question = False
                    else:
                        createFile = False
                        question = False
                else:
                    print "Please Enter 'y' or 'n'"
                    question = True
            if createFile:
                # Write updated data back to JSON file
                print "Updating JSON file:%s"%dataFile
                # Open JSON Data
                if os.path.exists(dataFile) and os.path.getsize(dataFile) > 0:
                    print "Writing data to JSON data file:%s" %dataFile
                else:
                    print "Creating JSON data to write to file:%s" %dataFile
                jsonfile=open(dataFile, 'w')
                json.dump(json.loads(cvpJSONdata), jsonfile, sort_keys = True, indent = 4, ensure_ascii = True)
                jsonfile.close()
                print "Updates Complete"
            print "Data creation completed:"
            if not options.test:
                if foundConfiglet:
                    print "Configlet %s updated: %s" %(options.configlet, changeConfiglet)
                else:
                    print "Configlet %s Created: %s" %(options.configlet, createConfiglet)
            print "File %s created: %s" %(dataFile, createFile)
    print "Excel data Creation and Import - Complete"
    if options.verbose:
        print "Verbose Mode"
    if options.test:
        print "Testing - CVP Data Configlets will not be Created"
        
if __name__ == '__main__':
    main()
