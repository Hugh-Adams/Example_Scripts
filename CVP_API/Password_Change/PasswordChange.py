#!/usr/bin/env python
#
# Copyright (c) 2017, Arista Networks, Inc.
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
# Device Local User's Password Change and Encryption
#
#    Version 0.0 11/12/2017
#            0.1 13/02/2018
# 
#    Written by:
#       Hugh Adams, Arista Networks
#
#    Revision history:
#       0.0 - initially script
#       0.1 - updated to use command line options and getpass to obscure password chanegs

# Import Required Libraries
import argparse
import getpass
import json
import requests
from requests import packages
from passlib.hash import sha512_crypt


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
        print "LogOut"
        headers = { 'Content-Type':'application/json' }
        logoutURL = "/cvpservice/login/logout.do"
        response = requests.post(self.url+logoutURL, cookies=self.cookies, json=self.authenticateData,headers=headers,verify=False)
        return response.json()

    def getConfiglet(self, name):
        getConfigletURL = "/cvpservice/configlet/getConfigletByName.do?"
        getConfigletParams = {'name':name}
        response = requests.get(self.url+getConfigletURL,cookies=self.cookies,params=getConfigletParams,verify=False)
        if "errorMessage" in str(response.json()):
            text = "(class-serverCvp-getConfiglet)-Error Configlet get failed: %s" % response.json()['errorMessage']
            raise serverCvpError(text)
        return response.json()

    def updateConfiglet (self, configletName, deviceKey, deviceConfig):
        headers = { 'Content-Type': 'application/json'}
        updateParams = {}
        updateURL = "/cvpservice/configlet/updateConfiglet.do"
        updateData = {"config":deviceConfig, "key":deviceKey, "name":configletName}
        response = requests.post(self.url+updateURL,cookies=self.cookies,json=updateData,headers=headers,params=updateParams, verify=False)
        if "errorMessage" in str(response.json()):
            text = "(class-serverCvp-updateConfiglet)-Error Configlet update failed: %s" % response.json()['errorMessage']
            raise serverCvpError(text)
        return response.json()

    def getUser (self, userID):
        headers = { 'Content-Type': 'application/json'}
        getURL = "/cvpservice/user/getUser.do?"
        getParams = {'userId':userID}
        response = requests.get(self.url+getURL,cookies=self.cookies,params=getParams,verify=False)
        if "errorMessage" in str(response.json()):
            text = "(class-serverCvp-getUser)-Error get User failed: %s" % response.json()['errorMessage']
            if response.json()['errorCode'] == "202801":
                return "NotFound"
            else:
                raise serverCvpError(text)
        else:
            return response.json()

    def updateUser (self, userID, email, userStatus, password, roles):
        headers = { 'Content-Type': 'application/json'}
        updateParams = {"userId":userID}
        updateURL = "/cvpservice/user/updateUser.do?"
        updateData = {"user":{"userId":userID,"email":email,"userStatus":userStatus, "password":password},"roles":roles}
        response = requests.post(self.url+updateURL,cookies=self.cookies,json=updateData,headers=headers,params=updateParams, verify=False)
        if "errorMessage" in str(response.json()):
            text = "(class-serverCvp-updateUser)-Error User update failed: %s" % response.json()['errorMessage']
            raise serverCvpError(text)
        else:
            return response.json()

    def createTask (self):
        headers = { 'Content-Type': 'application/json'}
        taskURL = "/cvpservice/provisioning/v2/saveTopology.do"
        taskData = []
        response = requests.post(self.url+taskURL,cookies=self.cookies,json=taskData,headers=headers, verify=False)
        if "errorMessage" in str(response.json()):
            text = "(class-serverCvp-createTask)-Error Task Creation failed: %s" % response.json()['errorMessage']
            raise serverCvpError(text)
        else:
            return response.json()

def askPass( user, host ):
   prompt = "Password for user {} on host {}: ".format( user, host )
   password = getpass.getpass( prompt )
   return password

def changePass( user):
   prompt = "  Please enter New Password for {}: ".format(user)
   password = getpass.getpass( prompt )
   return password

def main():
    # Set Intial Variables required

    # Set Intial Variables required
    getCvpAccess = True
    getCvpAppliance = True
    cvpAppList = []

    # Configure the option parser for CLI options to the script
    usage = "usage: %prog [options] username password appList configlet"
    parser = argparse.ArgumentParser(description="Local User Password Change and Encryption")
    parser.add_argument("--userName", help='Username to log into CVP')
    parser.add_argument("--password", help='Password for specified user to login')
    parser.add_argument("--appList",  help='List of CVP appliances to amend URL,URL')
    parser.add_argument("--configlet", help='Configlet name for device local users')
    args = parser.parse_args()

    # React to the options provided
    # Break Glass CVP configlet that has user names and passwords
    if args.configlet == None:
        configlet = raw_input("Name of Configlet containing local user: ")
    else:
        configlet = args.configlet
    # CVP Username for script to use
    if args.userName == None:
        userName = "cvpadmin"
    else:
        userName = args.userName
    # CVP Password for script to use
    if args.password == None:
        getCvpAccess = True
    else:
        password = args.password
        getCvpAccess = False
        # CVP Password for script to use
    if args.appList == None:
        getCvpAppliance = True
    else:
        cvpAppList = args.appList.split(",")
        getCvpAppliance = False

    print "Password Entries for Break Glass User Update"
    print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n"

# If CVP user credentials and Appliance list have not be paased to the script get them

    if getCvpAccess:
        userName = raw_input("User Name to Access CVP: ")
        password = askPass(userName, "CVP")

    if getCvpAppliance:
        applianceNumber = int(raw_input("Number of CVP Appliance to use: "))
        loop = 0
        while loop < applianceNumber:
            cvpAppList.append(raw_input("CVP Appliance %s: " %(loop+1)))
            loop += 1

    print "\nAll required parameters recieved, thank you\n"

# Login into each CVP instance in turn and update passwords

    print"\nRetrieving CVP Configlets"

    for appliance in cvpAppList:
        print"  conecting to %s" %appliance
        try:
            cvpSession = serverCvp(str(appliance),userName,password)
            logOn = cvpSession.logOn()
        except serverCvpError as e:
            print"   Connnection to %s:%s" %(appliance,e.value)
        # Get configlet with Break Glass usrs in
        print"  Colecting Break Glass Configlet"
        targetConfiglet = cvpSession.getConfiglet(configlet)
        configletKey = targetConfiglet["key"]
        # Display Configlet contents
        print"  Current Confliglet Contents"
        configLines = targetConfiglet["config"].splitlines()
        for line in configLines:
            print "    %s" %line
        print "\nUpdating Passwords:\n"
        # Work through each line of the configlet looking for users to update
        for index, line in enumerate(configLines):
            if "username" in line:
            # Get username and role details from config line
                username = line.split(None,2)[1]
                role = line.split("role",2)[1].split(None,2)[0]
            # Get privilege level if present in config line
                if "privilege" in line:
                    privilege = line.split("privelege",2)[1].split(None,2)[0]
            # Check to see if password needs changing
                question = True
                pwChange = False
                while question:
                    changePW = raw_input("    Do you want to change the password for %s (y/n): "%username)
                    if changePW in "yYnN":
                        if changePW in "yY":
                            pwChange = True
                        else:
                            pwChange = False
                        question = False
                    else:
                        print "Please Enter 'y' or 'n'"
                
                if pwChange:
                # Create new password for user if required
                    passCheck = True
                    while passCheck:
                        password1 = changePass(username)
                        password2 = changePass(username)
                        if password1 == password2:
                            passCheck = False
                            print "    Creating Password Hash\n"
                        else:
                            print "    Passwords do not match, please re-enter"
                # Create SHA512 hash of password
                    pwHash = sha512_crypt.using(rounds = 5000,salt_size=16).hash(password1)
                    print "      username %s role %s secret sha512 %s\n\n" %(username,role,pwHash)
                    configLines[index] = "username %s role %s secret sha512 %s" %(username,role,pwHash)
                # Update CVP user to be in sync with password changes
                    user = cvpSession.getUser(username)
                    if "NotFound" in user:
                        print "User %s not a CVP user\n\n" %username
                    elif username in "cvpadmin":
                        print "'cvpadmin' user is a special case please update password manually"
                        print "'cvpadmin' password has been configured to: %s\n" %password
                    else:
                        print "Updating user %s password in CVP %s" %(username, appliance) 
                        email = user["user"]["email"]
                        userStatus = user["user"]["userStatus"]
                        roles = user["roles"]
                        userUpdate = cvpSession.updateUser(username, email, userStatus, password, roles)
                        if "success" in userUpdate["data"]:
                            print "      Password updated\n"
                        else:
                            print "Password Update failed: %s\n" %userUpdate["data"]

        print"  New Confliglet Contents"
        # Create new Configlet from original plus password updates and update CVP
        newConfiglet = ""
        for line in configLines:
            print "    %s" %line
            newConfiglet = newConfiglet + line + "\n"
        configletUpdate = cvpSession.updateConfiglet(configlet, configletKey, newConfiglet)
        print "Updating Password Configlet: %s" %configlet
        print "Creating Tasks ready to push change to devices"
        # Added to script incase auto Task were not created
        question = False
        deviceChange = False
        while question:
            changeDevice = raw_input("    Do you want to create change tasks for devices on %s (y/n): "%appliance)
            if changeDevice in "yYnN":
                if changeDevice in "yY":
                    deviceChange = True
                else:
                    deviceChange = False
                question = False
            else:
                print "Please Enter 'y' or 'n'"
        if deviceChange:
            tasks = cvpSession.createTask()
            print "      Created Tasks: %s"%tasks["data"]["taskIds"]
        else:
            print "      Please Remeber to create tasks in cvp"
        # Close session with current CVP application
        cvpSession.logOut
        
        
if __name__ == '__main__':
    main()
