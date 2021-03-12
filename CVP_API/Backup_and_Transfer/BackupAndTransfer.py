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
# BAckup and File copy for CVP
#
#    Version 0.4 26/10/2018
# 
#    Written by:
#       Hugh Adams, Arista Networks
#
#    Revision history:
#       0.1 - initially script
#       0.2 - addition of Backup pruning option
#       0.3 - fix to identify end of backup in 2018.1.0
#       0.4 - fix to remove orphan backup creation

# Requires a user "backup" with access to files created on CVP
# Requires
# File location /data/cvpbackup/


# Import Required Libraries
import argparse
import getpass
import sys
import json
import requests
from requests import packages
import paramiko
from scp import SCPClient
from time import sleep 


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

    def getBackupList (self):
        headers = { 'Content-Type': 'application/json'}
        getURL = "/cvpservice/cvpbackuprestore/getAllBackupList.do?"
        getParams = {'startIndex':'0','endIndex':'0'}
        response = requests.get(self.url+getURL,cookies=self.cookies,params=getParams,verify=False)
        if "errorMessage" in str(response.json()):
            text = "(class-serverCvp-getBackupList)-Error get Backup List failed: %s" % response.json()['errorMessage']
            if response.json()['errorCode'] == "202801":
                return "NotFound"
            else:
                raise serverCvpError(text)
        else:
            return response.json()

    def createBackup (self):
        headers = { 'Content-Type': 'application/json'}
        postParams = {}
        postURL = "/cvpservice/cvpbackuprestore/backup.do"
        postData = {}
        response = requests.post(self.url+postURL,cookies=self.cookies,json=postData,headers=headers,params=postParams, verify=False)
        if "errorMessage" in str(response.json()):
            text = "(class-serverCvp-createBackup)-Error Backup failed: %s" % response.json()['errorMessage']
            raise serverCvpError(text)
        else:
            return response.json()

    def deleteBackup (self, backupId):
        headers = { 'Content-Type': 'application/json'}
        postParams = {}
        postURL = "/cvpservice/cvpbackuprestore/delete.do"
        postData = {"data":[{"backupId":backupId}]}
        response = requests.post(self.url+postURL,cookies=self.cookies,json=postData,headers=headers,params=postParams, verify=False)
        if "errorMessage" in str(response.json()):
            text = "(class-serverCvp-deleteBackup)-Error Backup Delete failed: %s" % response.json()['errorMessage']
            raise serverCvpError(text)
        else:
            return response.json()
        
    def getBackupProgress (self,eventId):
        headers = { 'Content-Type': 'application/json'}
        getURL = "/cvpservice/event/getEventDataById.do?"
        getParams = {'startIndex':'0','endIndex':'0','eventId':eventId}
        response = requests.get(self.url+getURL,cookies=self.cookies,params=getParams,verify=False)
        if "errorMessage" in str(response.json()):
            text = "(class-serverCvp-getBackupProgress)-Error get Backup Progress failed: %s" % response.json()['errorMessage']
            if response.json()['errorCode'] == "202801":
                return "NotFound"
            else:
                raise serverCvpError(text)
        else:
            return response.json()

    def getBackupStatus (self,eventId):
        headers = { 'Content-Type': 'application/json'}
        getURL = "/cvpservice/event/getEventById.do?"
        getParams = {'eventId':eventId}
        response = requests.get(self.url+getURL,cookies=self.cookies,params=getParams,verify=False)
        if "errorMessage" in str(response.json()):
            text = "(class-serverCvp-getBackupStatus)-Error get Backup Status failed: %s" % response.json()['errorMessage']
            if response.json()['errorCode'] == "202801":
                return "NotFound"
            else:
                raise serverCvpError(text)
        else:
            return response.json()

    def getBackupLog (self,backupId):
        headers = { 'Content-Type': 'application/json'}
        getURL = "/cvpservice/cvpbackuprestore/getLogs.do?"
        getParams = {'startIndex':'0','endIndex':'0','backupId':backupId}
        response = requests.get(self.url+getURL,cookies=self.cookies,params=getParams,verify=False)
        if "errorMessage" in str(response.json()):
            text = "(class-serverCvp-getBackupProgress)-Error get Backup Log: %s" % response.json()['errorMessage']
            if response.json()['errorCode'] == "252801":
                return "NotFound"
            else:
                raise serverCvpError(text)
        else:
            return response.json()

class SCPConnection(object):
    
    def __init__(self, host, username, password, port=22):
        """Initialize and setup connection"""
        self.scp_open = False
 
        # open SSH Transport stream
        self.transport = paramiko.Transport((host, port))
        if not self.scp_open:
            self.transport.connect(username=username, password=password)
            self.scp_open = True

    def put(self, local_file, remote_file):
        self.scp = SCPClient(self.transport)
        self.scp.put(local_file, remote_file)

    def get(self, local_file, remote_file):
        self.scp = SCPClient(self.transport)
        self.scp.get(remote_file, local_file)

    def close(self):
        """
        Close SFTP connection and ssh connection
        """
        if self.scp_open:
            self.transport.close()
            self.scp_open = False

class SFTPConnection(object):
    
    def __init__(self, host, username, password, port=22):
        """Initialize and setup connection"""
        self.sftp_open = False
 
        # open SSH Transport stream
        self.transport = paramiko.Transport((host, port))
        if not self.sftp_open:
            self.transport.connect(username=username, password=password)
            self.sftp_open = True

    def put(self, local_file, remote_file):
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)
        self.sftp.put(local_file, remote_file)

    def get(self, local_file, remote_file):
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)
        self.sftp.get(remote_file, local_file)

    def close(self):
        """
        Close SFTP connection and ssh connection
        """
        if self.sftp_open:
            self.transport.close()
            self.sftp_open = False

def askPass( user, host ):
   prompt = "Password for user {} on host {}: ".format( user, host )
   password = getpass.getpass( prompt )
   return password

def main():
    # Set Intial Variables required

    # Set Intial Variables required
    getCvpAccess = False
    getCvpAppliance = False
    getBackupAccess = False
    getDest = False
    getDestPath = False
    destination = "cvp"
    targetList = []
    destList = []

    # Configure the option parser for CLI options to the script
    usage = "usage: %prog [options] userName password backupUser backupPassword target destHost destPath xferOption limit"
    parser = argparse.ArgumentParser(description="Backup and Filecopy")
    parser.add_argument("--userName", required=True, help='Username to log into CVP')
    parser.add_argument("--password", help='Password for CVP user to login')
    parser.add_argument("--backupUser", help='Username to log into backup server')
    parser.add_argument("--backupPassword", help='Password for backup user to login')
    parser.add_argument("--target", help='List of CVP appliances to backup URL,URL')
    parser.add_argument("--destHost", help='List of URLs to copy backup to, set to localHost if run from server')
    parser.add_argument("--destPath", help='Directory to copy backup to')
    parser.add_argument("--xferOption", help='select sftp or scp transfer, default sftp')
    parser.add_argument("--limit", help='number of backups to retain, default 10, 0 - all')
    args = parser.parse_args()

    # React to the options provided
    # File Server Directory to copy back files to
    if args.destPath == None:
        getDestPath = True
    else:
        destPath = args.destPath
    # Backup Username for script to use
    if args.backupUser == None:
        getBackupAccess = True
    else:
        backupUser = args.backupUser
    # Backup Password for script to use
    if args.backupPassword == None:
        getBackupAccess = True
    else:
        # If pasword is between inverted commas remove them
        if (args.backupPassword[0] == args.backupPassword[-1]) and args.backupPassword.startswith(("'", '"')):
            backupPassword = args.backupPassword[1:-1]
        else:
             backupPassword = args.backupPassword
    # CVP Username for script to use
    if args.userName == None:
        getCvpAccess = True
    else:
        userName = args.userName
    # CVP Password for script to use
    if args.password == None:
        getCvpAccess = True
    else:
        if (args.password[0] == args.password[-1]) and args.password.startswith(("'", '"')):
            password = args.password[1:-1]
        else:
             password = args.password
    # CVP appliances to be backed up
    if args.target == None:
        getCvpAppliance = True
    else:
        targetList = args.target.split(",")

    # CVP appliances to be backed up
    if args.xferOption == None:
        xferOption = "sftp"
    else:
        xferOption = args.xferOption.lower()
    # File Server to copy back files to
    if args.destHost == None:
        getDest = True
    elif args.destHost.lower() == "localhost":
        destList = targetList
        destination = "remote"
    else:
        destList = args.destHost.split(",")

    # Number of backups to keep
    if args.limit == None:
        backupLimit = 10
    else:
        backupLimit = int(args.limit)

    print "Backup and File Copy Process"
    print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n"

# If CVP user credentials and Appliance list have not be paased to the script get them

    if getCvpAccess:
        userName = raw_input("User Name to Access CVP: ")
        password = askPass(userName, "CVP")

    if getCvpAppliance:
        applianceNumber = int(raw_input("Number of CVP Appliance to use: "))
        loop = 0
        while loop < applianceNumber:
            targetList.append(raw_input("CVP Appliance %s: " %(loop+1)))
            loop += 1

    if getBackupAccess and xferOption != "none":
        backupUser = raw_input("User Name for Backup Server: ")
        backupPassword = askPass(backupUser, "Backup Server")

    if getDest and xferOption != "none":
        destNumber = int(raw_input("Number of Destinations to copy backup files to: "))
        loop = 0
        while loop < destNumber:
            destList.append(raw_input("URL %s: " %(loop+1)))
            loop += 1

    if getDestPath and xferOption != "none":
        destPath = raw_input("Destination Backup Directory Path: ")

    print "\nAll required parameters received, thank you\n"

# Login into each CVP instance in turn and update passwords

    print"\nStarting CVP backup Processes"
    
    # Loop through CVP appliance, Create backup then copy files to servers
    for appliance in targetList:
        print"  connecting to %s" %appliance
        try:
            cvpSession = serverCvp(str(appliance),userName,password)
            logOn = cvpSession.logOn()
        except serverCvpError as e:
            print"   Connnection to %s:%s" %(appliance,e.value)
        
        # Get current number of backups completed
        print "Checking existing backup list..."
        try:
            backupList = cvpSession.getBackupList()
        except serverCvpError as e:
            print"   Backup Details %s:%s" %(appliance,e.value)
        if "NotFound" in backupList:
            print "No Backups found"
            backupCount = 0
        else:
            backupCount = int(backupList["total"])
        print "    There are %s completed Backups" %backupCount
 

        # Start a new backup
        try:
            backupJob = cvpSession.createBackup()
        except serverCvpError as e:
            print"   Create Backup %s:%s" %(appliance,e.value)
        eventId = backupJob["eventId"]
        fileSrc = backupJob["data"].rsplit(None,1)[1]+".zip"
        backupId = backupJob["data"].rsplit(None,1)[1].rsplit('/',1)[1]
        print "    Starting new backup: %s" %backupId

        # Monitor progress of backup
        # Loop round the backup job counting tasks completed
        # When all tasks are complete move on, could take some time
        completedCount = 0
        backupTaskCount = 1
        while completedCount < backupTaskCount:
            # reset completed count each iteration
            completedCount = 0
            # Allow backup to progress before checking
            sleep(10)
            try:
                backupProgress = cvpSession.getBackupProgress(eventId)
            except serverCvpError as e:
                print"   Monitor Backup %s:%s" %(appliance,e.value)
            backupTaskCount = backupProgress["total"]
            for task in backupProgress["data"]:
                if task['status'] =="COMPLETED":
                    completedCount +=1
            print "      %s of %s Tasks Completed" %(completedCount,backupTaskCount)
        print "      Backup Tasks Done"
        print "      Confiming Backup Complete"
        # Avoid looking at the Back Up list before the final backup step is completed as it creates a backup entry in the backup table.
        #This creates an orphan entry.To check completion of backup event check the status of the backup
        backupStatus = ''
        while backupStatus != 'COMPLETED':
            try:
                response = cvpSession.getBackupStatus(eventId)
                backupStatus = response['data']['status']
            except serverCvpError as e:
                print"      Backup Status %s:%s" %(appliance,e.value)
            sleep(1)
        print "      Backup now Completed"
        # Check for creation of backup zip file
        print "      Checking for new backupfile: %s" %fileSrc
        print "      This may take some time (5 minutes approx)"
        # Check that the backup appears in the Backup list before progressing
        secondCount = 0
        while secondCount <= backupCount:
            try:
                backupList = cvpSession.getBackupList()
            except serverCvpError as e:
                print"   Backup Details %s:%s" %(appliance,e.value)
            secondCount = int(backupList["total"])

        # Check that the backup log for the creation of the zip file
        zipNotFound = True
        while zipNotFound:
            try:
                backupLog = cvpSession.getBackupLog(backupId)
            except serverCvpError as e:
                print"   Backup Details %s:%s" %(appliance,e.value)
            if "NotFound" in backupLog:
                pass
            # CVP 2017.x.x returned "Backup Complete" at the end of the backup
            elif "Backup completed." in backupLog["data"][0]["activity"]:
                print "      Backup progress: %s" %backupLog["data"][0]["activity"]
                zipNotFound = False
                backupCount += 1
            # CVP 2018.1.x returned "Deleted temp folders successfully" at the end of the backup
            elif "Deleted temp folders successfully" in backupLog["data"][0]["activity"]:
                print "      Backup progress: %s - Backup completed" %backupLog["data"][0]["activity"]
                zipNotFound = False
                backupCount += 1
            else:
                print "      Backup progress: %s" %backupLog["data"][0]["activity"]

        # Copy back file to SCP server
        if xferOption == "none":
            print "Copy option 'none' selected: File Copy not required"
        else:
            print "Copying Backup file to Server"
            print "Backup file: %s" %fileSrc
            # filePath - provided by backup job details
            # fileDest - Server URL including directory
            for node in destList:
                if xferOption == "scp":
                    print "SCP option selected"
                    scp = SCPConnection(node, backupUser, backupPassword)
                    # The backupzip file may not be ready straight away, retry until it appears
                    # Not completely foolproof, could do to be refined
                    retryFile = True
                    while retryFile:
                        retryFile = False
                        try:
                        # If running on CVP choose 'put' option otherwise use get
                            if destination == "remote":
                                # Remote
                                scp.get(destPath, fileSrc)
                            elif destination == "cvp":
                                # CVP
                                scp.put(fileSrc, destPath)
                            else:
                                print "destination not set: SCP Skipped"
                        # If the file does not exist retry the copy all other errors stop.
                        except OSError as e:
                            if "No such file or directory" in e:
                                print "Looking for file"
                                retryGet = True
                            else:
                                print "      Problem with SCP: %s" %e
                    print "Copy complete destination - %s:/%s%s.zip" %(node,destPath,backupId)
                    scp.close()
                elif xferOption == "sftp":
                    print "SFTP option selected"
                    sftp = SFTPConnection(node, backupUser, backupPassword)
                    # The backupzip file may not be ready straight away, retry until it appears
                    # Not completely foolproof, could do to be refined
                    retryFile = True
                    while retryFile:
                        retryFile = False
                        try:
                        # If running on CVP choose 'put'option otherwise use get
                        # For SFTP need destination to include file as well as path
                            destFile = destPath+backupId+".zip"
                            if destination == "remote":
                                # Remote
                                sftp.get(destFile, fileSrc)
                            elif destination == "cvp":
                                # CVP
                                sftp.put(fileSrc, destFile)
                            else:
                                print "destination not set: SFTP Skipped"
                        # If the file does not exist retry the copy all other errors stop.
                        except OSError as e:
                            if "No such file or directory" in e:
                                print "Looking for file"
                                retryGet = True
                            else:
                                print "      Problem with SFTP: %s" %e
                    print "Copy complete destination - %s:/%s%s.zip" %(node,destPath,backupId)
                    sftp.close()
                else:
                    print "No Valid copy option selected: %s" %xferOption


        # Tidy up old backups - clear the oldest backups so that there are only 'limt' or less backups.
        if backupLimit > 0:
            skipCount = 0
            print "Number of backups: %s Number Required: %s" %(backupCount, backupLimit)
            while int(backupCount) > backupLimit:
                # Delete the last backup
                # Sort the backup list by key as it increments each time then get the first entry
                # If the first entry is the current backup skip to the next one, this avoids an issue in the API
                backupSorted = sorted(backupList["data"], key=lambda k: k['key'],reverse=False)
                if len(backupSorted) > skipCount: 
                    targetBackup = backupSorted[skipCount]["key"]
                    location = backupSorted[skipCount]["location"]
                if backupId in targetBackup:
                    print "Current Backup found: %s - Will not Delete" %backupId
                    skipCount += 1
                    backupLimit +=1
                if backupId in location:
                    print "Current Backup File found: %s - Will not Delete" %backupId
                    skipCount += 1
                    backupLimit += 1
                else:
                    print "Deleted old backup: %s" %targetBackup
                    # delete the first (oldest) backup in the list
                    cvpSession.deleteBackup (targetBackup)
                    # wait for CVP to complete the deletion then check to see if the backup has been removed
                    wait = True
                    while wait:
                        sleep(1)
                        try:
                            backupList = cvpSession.getBackupList()
                        except serverCvpError as e:
                            print"   Backup Details %s:%s" %(appliance,e.value)
                        if targetBackup in backupList:
                            wait = True
                        else:
                            wait = False
                backupCount = int(backupList["total"])
        else:
            print "keeping all %s backups" %backupCount

                


        # Close session with current CVP application
        cvpSession.logOut
        
        
if __name__ == '__main__':
    main()
