#! /usr/bin/env python
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
# Configlet String Search and Config Save
#
#    Version 0.0 8/03/2019
#
#    Written by:
#       Hugh Adams, Arista Networks
#
#    Revision history:
#       0.0 - initially script
# Tool to search configlets for a given string and save configlets config to text file
# Or download Configlet Configs based on string in configlet name

# Works with CVP 2018.1.4

# Import Required Libraries

import argparse
import getpass
import re
import json
import requests
from requests import packages
import os, csv, sys


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
        '''Returns a Configlet, Configlet Builder, Configlet Builder Configlet'''
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

    def searchConfiglets (self, configletType="", searchString=False):
        '''Returns a list of Configlet data that matches on Configlet Type and Search String
           if nothing matches or no string provided an error code is returned'''
        configletData = []
        searchResults = []
        #filterConfiglet = True
        if searchString:
        # Gather the configlets to be searched, either all of them
            if configletType in ("all","All"):
                configletType = ""
                filterConfiglet = False
            configletData = self.getConfigletList(configletType)["data"]
            # Search through list of configlets looking for string, record configlet name and line number if string found
            if configletData:
                for configlet in configletData:
                    for number,line in enumerate(re.split('\n', configlet['config'])):
                        if searchString in line:
                            searchResults.append([configlet['name'],number,line,configlet['config']])
                            #print configlet['name']
            if len(searchResults) > 0:
                return searchResults
            else:
                notFound = {"data":{"errorCode":99999,"errorMessage":"Nothing Found"}}
                return notFound
        else:
            notFound = {"data":{"errorCode":99999,"errorMessage":"Search String not defined"}}
            return notFound

    def exportConfiglets (self, configletType=""):
        '''Returns a list of Configlet data that matches on Configlet Type
           if nothing matches or no string provided an error code is returned'''
        configletData = []
        configletResults = []
        # Gther the configlets, all of them
        if configletType in ("all","All"):
            configletType = ""
            configletData = self.getConfigletList(configletType)["data"]
        # Or the one that match the configletType
        else:
            for configlet in self.getConfigletList(configletType)["data"]:
                configletResults.append([configlet['name'],configlet['config']])
        if len(configletResults) > 0:
            return configletResults
        else:
            notFound = {"data":{"errorCode":99999,"errorMessage":"Nothing Found"}}
            return notFound


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
    parser = argparse.ArgumentParser( description='CVP Search Configlets and tool' )
    parser.add_argument( '--host', default=None, help='Hostname or IP address of CVP' )
    parser.add_argument( '--user', default=None, help='CVP user username' )
    parser.add_argument( '--password', default=None, help='password corresponding to the CVP username' )
    parser.add_argument( '--Ctype', help='Type of Configlet, Static, Builder, Generated, or All',
                        default="All" )
    parser.add_argument( '--search', default=None, help='String to match in configlet')
    parser.add_argument( '--retrieve', default=False, help='Save Matching Configlet (True/False)')
    args = parser.parse_args()
    return checkArgs( args )

def askPass( user, host ):
    """Simple function to get missing password if not recieved as a CLI option"""
    prompt = "Password for user {} on host {}: ".format( user, host )
    password = getpass.getpass( prompt )
    return password

def checkArgs( args ):
    '''check the correctness of the input arguments'''
    if args.host == None:
       args.host = raw_input("Please Enter a URL or IP for CVP: ")
    if not args.Ctype in ['Static','Builder','Generated','All','all']:
       print 'Error: Configlet Type "--Ctype" is incorrect, options are (Static Builder Generated All)'
       sys.exit( 2 )
    if args.user is None:
       args.user = raw_input("Please Enter a User Name for CVP: ")
    if args.search is None:
       args.search = raw_input("Please Enter a search string: ")
    else:
        if (args.search[0] == args.search[-1]) and args.search.startswith(("'", '"')):
            args.search = args.search[1:-1]
    if args.password is None:
       args.password = askPass( args.user, args.host )
    return args


def main( ):
    '''Get command options, retrieve configlet data and create and exportlist, export confilets to
       a Zip file then copy zip file to a remote host'''
    # Get CLI options
    options = parseArgs()
    fullPath = os.path.abspath(os.path.dirname(sys.argv[0]))
    print"Connecting to %s" %options.host
    # Connecting to CVP
    try:
      cvpSession = serverCvp(options.host,options.user,options.password)
      logOn = cvpSession.logOn()
    except serverCvpError as e:
      print"  Connnection to %s:%s" %(options.host,e.value)
      sys.exit(2)

    # Create Configlet Export file
    if "all-" in options.search.lower():
        configResults = cvpSession.exportConfiglets(options.Ctype)
        if "errorMessage" in str(configResults):
            print "Configlet Search Failed: %s" %configResults['data']['errorMessage']
        else:
            # ([configlet['name'],configlet['config']])
            print "Found %s Configlets:\n" %(len(configResults))
            configletFilter = re.split('-',options.search)[1]
            for item in configResults:
                if configletFilter in item[0]:
                    print "Configlet Name: %s Found" %item[0]
                    if options.retrieve:
                        print "Saving Configlet %s" %item[0]
                        filePath = "%s/%s_config.txt" %(fullPath,item[0])
                        saveConfiglet = fileWrite(filePath,item[1],"txt","w")
                        if saveConfiglet:
                            print "Configlet Config saved to: %s" %filePath
    else:
        searchResults = cvpSession.searchConfiglets(options.Ctype, options.search)
        if "errorMessage" in str(searchResults):
            print "Configlet Search Failed: %s" %searchResults['data']['errorMessage']
        else:
            # Display search results configlet name and line
            # ([configlet['name'],number,line,configlet['config']])
            print "Search for %s found %s Results:-" %(options.search, len(searchResults))
            for item in searchResults:
                print "\n\nConfiglet Name: %s \n   Line Number %s" %(item[0],item[1])
                print "   Config Line: %s" %item[2]
                if options.retrieve:
                    print "   Saving Configlet %s" %item[0]
                    filePath = "%s/%s_config.txt" %(fullPath,item[0])
                    saveConfiglet = fileWrite(filePath,item[3],"txt","w")
                    if saveConfiglet:
                        print "   Configlet Config saved to: %s" %filePath

    # Logout of CVP
    cvpSession.logOut

if __name__ == '__main__':
    main()
