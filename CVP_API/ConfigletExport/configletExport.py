#! /usr/bin/env python
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
# Configlet Download
#
#    Version 0.0 12/02/2018
# 
#    Written by:
#       Hugh Adams, Arista Networks
#
#    Revision history:
#       0.0 - initially script
# Tool to retrieve configlets and configlet builders

# Import Required Libraries

import sys
import os
import argparse
import getpass
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
        ''' Create session to the host, ignoring any certificate errors'''
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
        '''Calls authentication API and traps any issues, also generates the session cookies required'''
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
        '''Clears sessions with CVP server using the session cookies'''
        print "LogOut"
        headers = { 'Content-Type':'application/json' }
        logoutURL = "/cvpservice/login/logout.do"
        response = requests.post(self.url+logoutURL, cookies=self.cookies, json=self.authenticateData,headers=headers,verify=False)
        return response.json()

    def getConfigletList(self, configletType=""):
        '''Returns a list of Configlet, Configlet Builders, Configlet Builder Configlets'''
        # configletType - Static = normal configlet
        # configletType - Generated = ConfigletBuilder configlet
        # configletType - Builder = ConfigletBuilder
        headers = { 'Content-Type': 'application/json'}
        getURL = "/cvpservice/configlet/getConfiglets.do?"
        getParams = {'type':configletType,'startIndex':0, 'endIndex':0}
        response = requests.get(self.url+getURL,cookies=self.cookies,params=getParams,verify=False)
        if "errorMessage" in str(response.json()):
            text = "(class-serverCvp-getConfigletList)-Error get Configlet List failed: %s" % response.json()['errorMessage']
            raise serverCvpError(text)
        else:
            return response.json()
        
    def getConfiglet(self, configletName):
        '''Returns a list of Configlet, Configlet Builders, Configlet Builder Configlets'''
        # configletType - Static = normal configlet
        # configletType - Generated = ConfigletBuilder configlet
        # configletType - Builder = ConfigletBuilder
        headers = { 'Content-Type': 'application/json'}
        getURL = "/cvpservice/configlet/getConfigletByName.do?"
        getParams = {'name':configletName}
        response = requests.get(self.url+getURL,cookies=self.cookies,params=getParams,verify=False)
        if "errorMessage" in str(response.json()):
            text = "(class-serverCvp-getConfiglet)-Error get Configlet by Name failed %s: %s" % (configletName, response.json()['errorMessage'])
            print text
            return "BadName"
        else:
            return response.json()

    def exportConfiglets (self, configletType="", configletList=["all"]):
        '''Returns a list of Configlet data that matches on Configlet Type and Configlet Name
           passed to the function as configletList, if nothing matches an error code is returned'''
        configletKeyList = []
        configletData = []
        filterConfiglet = True
        if configletType in ("all","All"):
            configletType = ""
            filterConfiglet = False
        if configletList[0] in ("all","All"):
            configletData = self.getConfigletList(configletType)["data"]
        else:
            for name in configletList:
                configlet = self.getConfiglet(name)
                if not("BadName" in configlet):
                    configletData.append(configlet)
        if configletData:
            for configlet in configletData:
                if filterConfiglet:
                    if configlet['type'] in configletType:
                        configletKeyList.append(configlet["key"])
                else:
                    configletKeyList.append(configlet["key"])
        if len(configletKeyList) > 0:
            headers = { 'Content-Type': 'application/json'}
            updateParams = {}
            updateURL = "/cvpservice/configlet/exportConfiglets.do"
            updateData = {"data":configletKeyList}
            response = requests.post(self.url+updateURL,cookies=self.cookies,json=updateData,headers=headers,params=updateParams, verify=False)
            if "errorMessage" in str(response.json()):
                text = "(class-serverCvp-exportConfiglets)-Error Export Configlets failed:(%s)" % response.json()
                raise serverCvpError(text)
            else:
                return response.json()
        else:
            notFound = {"data":{"errorCode":99999,"errorMessage":"Nothing to Export"}}
            return notFound

    def getElement(self, elementName=""):
        '''Returns data about Elements that match the string passed to it, if blank empty list returned,
           if nothing found list of empty keys returned'''
        # If element is a device, device info will be returned
        # If element is a container multi device info will be returned
        headers = { 'Content-Type': 'application/json'}
        getURL = "/cvpservice/provisioning/searchTopology.do?"
        getParams = {'queryParam':elementName, 'startIndex':0, 'endIndex':0}
        response = requests.get(self.url+getURL,cookies=self.cookies,params=getParams,verify=False)
        if "errorMessage" in str(response.json()):
            text = "(class-serverCvp-getElement)-Error get Element Info failed: %s" % response.json()['errorMessage']
            raise serverCvpError(text)
        else:
            return response.json()

    def getInventoryItem(self, searchString=""):
        '''Lazy match search of Inventory Items, can returm more than one, if searchstring empty will return all items'''
        headers = { 'Content-Type': 'application/json'}
        getURL = "/cvpservice/inventory/getInventory.do?"
        getParams = {'startIndex':0, 'endIndex':0, 'queryparam':searchString}
        response = requests.get(self.url+getURL,cookies=self.cookies,params=getParams,verify=False)
        if "errorMessage" in str(response.json()):
            text = "(class-serverCvp-getInventoryItem)-Error get Inventory Item failed: %s" % response.json()['errorMessage']
            raise serverCvpError(text)
        else:
            if response.json()['total'] > 0:
                return response.json()
            else:
                return False

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
        """Creates an SCP sessions then copies the local file to
           the remote file"""
        self.scp = SCPClient(self.transport)
        self.scp.put(local_file, remote_file)

    def get(self, local_file, remote_file):
        """Creates an SCP sessions then copies the remote file to
           the local file"""
        self.scp = SCPClient(self.transport)
        self.scp.get(remote_file, local_file)

    def close(self):
        """
        Close SCP connection and SSH connection
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
        """Create an SFTP session then copies the local file to the remote file
           both remote and local file paths have to include the filename"""
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)
        self.sftp.put(local_file, remote_file)

    def get(self, local_file, remote_file):
        """Create an SFTP session then copies the remote file to the local file
        both remote and local file paths have to include the filename"""
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)
        self.sftp.get(remote_file, local_file)

    def close(self):
        """
        Close SFTP connection and ssh connection
        """
        if self.sftp_open:
            self.transport.close()
            self.sftp_open = False

def parseArgs():
    """Gathers comand line options for the script, generates help text and performs some error checking"""
    parser = argparse.ArgumentParser( description='CVP Get Configlets and Builders tool' )
    parser.add_argument( '--host', default='localhost', help='Hostname or IP address of CVP' )
    parser.add_argument( '--user', required=True, help='CVP user username' )
    parser.add_argument( '--password', default=None, help='password corresponding to the CVP username' )
    parser.add_argument( '--configlets', nargs='*', help='list of configlet names',
                        metavar='CONFIGLETS', default=["All"] )                                  
    parser.add_argument( '--Ctype', help='Type of Configlet, Static, Builder, Generated, or All',
                        default="All" )
    parser.add_argument("--copyHost", default="localhost", help='URL or IP of host for copying Configlets')
    parser.add_argument("--destPath", required=True, help='Directory to copy Configlets to')
    parser.add_argument("--xferOption", default="scp", help='select sftp or scp transfer, default sftp')
    parser.add_argument("--copyUser", help='Username to log into copy host')
    parser.add_argument("--copyPassword", default=None, help='Password for copy user to login')                                       
    args = parser.parse_args()
    return checkArgs( args )

def askPass( user, host ):
    """Simple function to get missing password if not recieved as a CLI option"""
    prompt = "Password for user {} on host {}: ".format( user, host )
    password = getpass.getpass( prompt )
    return password

def checkArgs( args ):
    '''check the correctness of the input arguments'''
    if (args.host == 'localhost' and args.copyHost == 'localhost'):
       print 'Error: Both host and destHost should not be set to localhost'
       sys.exit( 2 )
    if not args.Ctype in ['Static','Builder','Generated','All','all']:
       print 'Error: Configlet Type "--Ctype" is incorrect, options are (Static Builder Generated All)'
       sys.exit( 2 )
    if args.password is None:
       args.password = askPass( args.user, args.host )
    if args.copyPassword is None:
       args.copyPassword = askPass( args.copyUser, args.copyHost )
    return args


def main( ):
    '''Get command options, retrieve configlet data and create and exportlist, export confilets to
       a Zip file then copy zip file to a remote host'''
    # Get CLI options
    options = parseArgs()
    print"Connecting to %s" %options.host
    # Connecting to CVP
    try:
      cvpSession = serverCvp(options.host,options.user,options.password)
      logOn = cvpSession.logOn()
    except serverCvpError as e:
      print"  Connnection to %s:%s" %(options.host,e.value)

    # Create Configlet Export file
    exportFile = cvpSession.exportConfiglets(options.Ctype, options.configlets)
    if "errorMessage" in str(exportFile):
        print "Configlet Export Failed: %s" %exportFile['data']['errorMessage']
    else:
        # fileSrc - provided by exportConfiglets job details
        # destFile - Server URL including directory
        fileSrc = exportFile['data']
        destFile = exportFile['data'].split("/")[-1]
        print "   Tempoary export file cretated: %s" %fileSrc
        # Copy Configlet Export file to destination
        print "Copying Configlet Export file to %s:%s"%(options.copyHost,options.destPath)
        if options.xferOption == "scp":
            if options.copyHost == "localhost":
                transferHost = options.host
            else:
                transferHost = options.copyHost
            scp = SCPConnection(transferHost, options.copyUser, options.copyPassword)
            # The Configletzip file may not be ready straight away, retry until it appears
            # Not completely foolproof, could do to be refined
            retryFile = True
            while retryFile:
                retryFile = False
                try:
                # Check to see where the copy is originating from
                # If running on CVP choose 'put' option otherwise use get
                    if options.copyHost == "localhost":
                        # Remote
                        scp.get(options.destPath, fileSrc)
                    else:
                        # CVP
                        scp.put(fileSrc, options.destPath)
                # If the file does not exist retry the copy all other errors stop.
                except OSError as e:
                    if "No such file or directory" in e:
                        print "Looking for file"
                        retryGet = True
                    else:
                        print "      Problem with SCP: %s" %e
                # Wait a few seconds before trying again
                sleep(2)
            print "Copy complete destination - %s:%s" %(transferHost,options.destPath)
            scp.close()
        elif xferOption == "sftp":
            sftp = SFTPConnection(transferHost, options.copyUser, options.copyPassword)
            # The Configletzip file may not be ready straight away, retry until it appears
            # Not completely foolproof, could do to be refined
            retryFile = True
            while retryFile:
                retryFile = False
                try:
                # If running on CVP choose 'put'option otherwise use get
                # For SFTP need destination to include file as well as path
                    destFilePath = options.destPath+destFile
                    if options.copyHost == "localhost":
                        # Remote
                        sftp.get(destFilePath, fileSrc)
                    else:
                        # CVP
                        sftp.put(fileSrc, destFilePath)
                # If the file does not exist retry the copy all other errors stop.
                except OSError as e:
                    if "No such file or directory" in e:
                        print "Looking for file"
                        retryGet = True
                    else:
                        print "      Problem with SFTP: %s" %e
                # Wait a few seconds before trying again
                sleep(2)
            print "Copy complete destination - %s:%s" %(transferHost,destFilePath)
            sftp.close()
        else:
            print "No copy option selected"


        # If on the CVP appliance Tidy up Configlet Zip files.
        if options.host == 'localhost':
            print "Deleting Temporary Zip file: %s" %fileSrc
            try:
                os.remove(fileSrc)
            except OSError as e:
                print "Error: %s - %s"%(fileSrc, e)
            

    # Logout of CVP
    cvpSession.logOut

if __name__ == '__main__':
    retval = main()
    sys.exit( retval )
