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
# Reconcile Configlet Rename
#
#    Version 0.0 12/02/2018
# 
#    Written by:
#       Hugh Adams, Arista Networks
#
#    Revision history:
#       0.0 - initially POC script
#
# Tool to rename RECONCILE configilets fro RECONCILE_<IPaddress> to RECONCILE_<hostName>
#

# Import Required Libraries


import argparse
import getpass
import json
import requests

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
            error['data']['errorMessage']=text
            return error
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
            error['data']['errorMessage']=text
            return error
        else:
            return response.json()

    def getAppliedDevices(self, configletName):
        '''Returns a list of Configlet, Configlet Builders, Configlet Builder Configlets'''
        # configletType - Static = normal configlet
        # configletType - Generated = ConfigletBuilder configlet
        # configletType - Builder = ConfigletBuilder
        headers = { 'Content-Type': 'application/json'}
        getURL = "/cvpservice/configlet/getAppliedDevices.do?"
        getParams = {'configletName':configletName, 'startIndex':0, 'endIndex':0}
        response = requests.get(self.url+getURL,cookies=self.cookies,params=getParams,verify=False)
        if "errorMessage" in str(response.json()):
            text = "(class-serverCvp-getAppliedDevice)-Error get Configlet Applied Device failed %s: %s" % (configletName, response.json()['errorMessage'])
            error['data']['errorMessage']=text
            error['data']['errorCode']=response.json()['errorCode']
            error['data']['total']=0
            return error
        else:
            return response.json()

    def updateReconcileConfiglet (self, configletName, configletConfig, configletKey, hostKey):
        '''Returns a list of Configlet data that matches on Configlet Type and Configlet Name
           passed to the function as configletList, if nothing matches an error code is returned'''
        headers = { 'Content-Type': 'application/json'}
        updateParams = {"netElementId":hostKey}
        updateURL = "/cvpservice/provisioning/updateReconcileConfiglet.do?"
        updateData = {"name":configletName, "config":configletConfig, "key":configletKey,"reconciled": True}
        response = requests.post(self.url+updateURL,cookies=self.cookies,json=updateData,headers=headers,params=updateParams, verify=False)
        if "errorMessage" in str(response.json()):
            text = "(class-serverCvp-exportConfiglets)-Error Export Configlets failed:(%s)" % response.json()
            error['data']['errorMessage']=text
            return error
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
            error['data']['errorMessage']=text
            return error
        else:
            if response.json()['total'] > 0:
                return response.json()
            else:
                return False

def parseArgs():
    """Gathers comand line options for the script, generates help text and performs some error checking"""
    parser = argparse.ArgumentParser( description='CVP Get Configlets and Builders tool' )
    parser.add_argument( '--host', default='localhost', help='Hostname or IP address of CVP' )
    parser.add_argument( '--user', required=True, help='CVP user username' )
    parser.add_argument( '--password', default=None, help='password corresponding to the CVP username' )                                       
    args = parser.parse_args()
    return checkArgs( args )

def askPass( user, host ):
    """Simple function to get missing password if not recieved as a CLI option"""
    prompt = "Password for user {} on host {}: ".format( user, host )
    password = getpass.getpass( prompt )
    return password

def checkArgs( args ):
    '''check the correctness of the input arguments'''
    if args.password is None:
       args.password = askPass( args.user, args.host )
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

    # Search Provisioning Topology for configlets with the reconcile flag set.
    configletList = cvpSession.getConfigletList()
    if "errorMessage" in str(configletList):
        print "Get Configlet List Failed:\n %s" %configletList['data']['errorMessage']
    else:
        # Parse the list for reconcile configlets
        # reconcile flag is a True / False option
        # Create a list of configlets to change names on and create name from device name
        reconcileList = []
        for configlet in configletList['data']:
            configletDetail={}
            # While parsing data will check to see if name need changing and set flag.
            nameChange = True
            if configlet['reconciled']:
                print "   Found %s"%configlet['name']
                configletDetail['name'] = configlet['name']
                configletDetail['configletKey'] = configlet['key']
                configletDetail['configletConfig'] = configlet['config']
                # Need the applied device key and device name from the inventory
                # Get applied device detail
                appliedDevice = cvpSession.getAppliedDevices(configlet['name'])
                if "errorMessage" in str(appliedDevice):
                    print    "Get Applied Device Failed:\n %s" %appliedDevice['data']['errorMessage']
                    # Prevent name change as data was not avialable.
                    nameChange = False
                else:
                    print "     Found Device Details for %s"%appliedDevice['data'][0]['hostName']
                    configletDetail['hostName'] = appliedDevice['data'][0]['hostName']
                    configletDetail['hostIP']= appliedDevice['data'][0]['ipAddress']
                # Check Current configlet name, if it contains IP address it needs updating else not
                print "     Check %s is in %s"%(appliedDevice['data'][0]['ipAddress'],  configlet['name'])
                if appliedDevice['data'][0]['ipAddress'] in configlet['name']:
                    print "       Match"
                    # Get device key to use with Reconcile Configlet Update
                    # Use IP address as host Name may not get a unique match
                    deviceDetail = cvpSession.getInventoryItem(appliedDevice['data'][0]['ipAddress'])
                    if "errorMessage" in str(deviceDetail):
                        print "     Get Device Key Failed:\n %s" %deviceDetail['data']['errorMessage']
                        # Prevent name change as data was not avialable.
                        nameChange = False
                    elif deviceDetail['total']>1:
                        # Check that only one match made in search
                        print "     Get Device Key Failed:\n Too many matches on IP address"
                        # Prevent name change as data was not avialable.
                        nameChange = False
                    else:
                        print "     Found key - %s for %s"%(deviceDetail['netElementList'][0]['key'],\
                                                          appliedDevice['data'][0]['hostName'])
                        configletDetail['hostKey'] = deviceDetail['netElementList'][0]['key']
                else:
                    print "     NoMatch"
                    nameChange = False
                if nameChange:
                    # If name needs changing and all criteria has been found add to the list.
                    reconcileList.append(configletDetail)

        if len(reconcileList)>0:
            print "\n\nRenaming Reconcile Configlets"
            for configlet in reconcileList:
                configletName = "RECONCILE_%s"%configlet['hostName']
                reconcileRename = cvpSession.updateReconcileConfiglet(configletName, configlet['configletConfig'],\
                                                                  configlet['configletKey'], configlet['hostKey'])
                if "errorMessage" in str(reconcileRename):
                    print "   Rename %s to %s Failed:\n %s" %(configlet['name'], configletName,\
                                                           reconcileRename['data']['errorMessage'])
                else:
                    print "   Rename %s to %s Complete" %(configlet['name'], configletName)
                # Break added for debugging / demo reasons.
                # break
    # Logout of CVP
    logout = cvpSession.logOut
    if "errorMessage" in str(logout):
        print "Logout Failed:\n %s" %logout['data']['errorMessage']
    else:
        print "Disconected from CVP"

if __name__ == '__main__':
    retval = main()
    sys.exit( retval )
