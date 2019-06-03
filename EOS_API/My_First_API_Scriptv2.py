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

# Test Notes
# This script assumes 4.14.2F or later is on the switches.


# Imports
import argparse
import getpass
import sys
import ssl
import socket
import errno
import json
import re
from jsonrpclib import Server
import jsonrpclib

# Assign defaults
global USER
global PASSWORD
global HOST_PORT
USER = "admin"
PASSWORD = "arista"
HOST_PORT = 443

def runCommand(user, password, address, port, commands, output="json", protocol="https"):
    """ Function to connect to EAPI interface on a switch and send commands to it, the routine will return
        the output of each command in JSON format by default.
        user - username to access switch with, requires correct privledge level to run the required commands
        password - password for above user
        address - ip or url for target switch
        port - tcp port to access the EAPI interface, normally 443
        commands - list of commands to pass to the switch
        option - protocol to use for EAPI session http, https, or local (unix sockets)
        output - output format to be return by the EAPI options are txt or json """

    # Work arround for ssl.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:833)
    # import ssl

    ssl._create_default_https_context = ssl._create_unverified_context
    
    if protocol == "http":
        #Connect to Switch via HTTP eAPI
        switch = Server("http://"+user+":"+password+"@"+address+":"+str(port)+"/command-api")
    elif protocol == "https":
        #Connect to Switch via HTTPS eAPI
        switch = Server("https://"+user+":"+password+"@"+address+":"+str(port)+"/command-api")
    elif protocol == "local":
        # Connect to Switch via Unix Socket
        EAPI_SOCKET = 'unix:/var/run/command-api.sock'
        switch = Server(EAPI_SOCKET)
    # capture Connection problem messages:
    try:
        response = switch.runCmds(1,commands,output)
        jsonrpclib.history.clear()
    except socket.error, error:
        error_code = error[0]
        if error_code == errno.ECONNREFUSED: # Raise exception if connection is refused by switch
            con_error = str("[Error:"+str(error_code)+"] Connection Refused!(eAPI not configured?)")
        elif error_code == errno.EHOSTUNREACH: # Raise exception if switch is unreachable from host
            con_error = str("[Error:"+str(error_code)+"] No Route to Host(Switch powered off?)")
        elif error_code == errno.ECONNRESET: # Raise exception if connection is refset by the switch
            con_error = str("[Error:"+str(error_code)+"] Connection RST by peer (Restart eAPI)")
        elif error_code == 8: # Raise exception if switch hostname cannot be resolved in DNS
            con_error = str("[Error:"+str(error_code)+"] Host/Server name not resolved (Check DNS or Host File)")
        else:
            # Unknown error - report error number and error string (should capture all)
            con_error = str("[Error:"+str(error_code) + "] "+error[1])
        return con_error
    # Protcol errors - report error number and error string (catches command execution errors)
    except jsonrpclib.jsonrpc.ProtocolError:
        errorResponse = jsonrpclib.loads(jsonrpclib.history.response)
        prot_error = "[Protocol-Error:"+str(errorResponse["error"]["code"])+"] "+str(errorResponse["error"]["message"])
        return prot_error        
    else:
        return response
    
def parseArgs():
    """Gathers comand line options for the script, generates help text and performs some error checking"""
    # Configure the option parser for CLI options to the script
    usage = "usage: %prog [options] userName password site"
    parser = argparse.ArgumentParser(description="LInk Ping Test")
    parser.add_argument("--username", default=USER, help='Username to access switches') # Remove default option to get user prompt for this CLI input
    parser.add_argument("--password", default=PASSWORD, help='Password for user to access switches') # Remove default option to get user prompt for this CLI input
    parser.add_argument("--hosts" ,help='Switch(s) to run command(s)on')
    parser.add_argument("--command", help='Command to execute through API')
    args = parser.parse_args()
    return checkArgs( args )

def askPass( user, host ):
    """Simple function to get missing password if not recieved as a CLI option"""
    prompt = "Password for user {} to access {}: ".format( user, host )
    password = getpass.getpass( prompt )
    return password

def checkArgs( args ):
    """check the correctness of the input arguments"""
    getAccess = False

    # Switch Username for script to use
    if args.username == None:
        getAccess = True
        
    # Password for script to use
    if args.password == None:
        getAccess = True
    else:
        if (args.password[0] == args.password[-1]) and args.password.startswith(("'", '"')):
            password = args.password[1:-1]

    # If username or password not given prompt for them before proceeding
    if getAccess:
        args.username = raw_input("User Name to access switch: ")
        args.password = askPass( args.userName, "switch" )

    # If target switches not provided
    if args.hosts == None:
        args.hosts = []
        hostNumber = int(raw_input("Number of Switches to use: "))
        loop = 0
        while loop < hostNumber:
            args.hosts.append(raw_input("Switch URL/IP %s: " %(loop+1)))
            loop += 1
    else:
        if (args.hosts[0] == args.hosts[-1]) and args.hosts.startswith(("'", '"')):
                    args.hosts = args.hosts[1:-1]
        hosts = args.hosts
        if "," in hosts:
            args.hosts = re.split(',',args.hosts)
        else:
            args.hosts = [hosts] # Create a list of hosts instead of a text string

    # Command options for script to use
    if args.command== None:
        args.command = []
        print "No Command Entered 'show version' will be used"
        args.command = "show version"
    else:
        if (args.command[0] == args.command[-1]) and args.command.startswith(("'", '"')):
                args.command = args.command[1:-1]
    commands = args.command
    if "," in commands:
        args.command = re.split(',',args.command)
    else:
        args.command = [commands] # Create a list of command instead of a text string

    return args

# Main Function

def main():

    # Set Intial Variables required from command line optons
    options = parseArgs()
    for device in options.hosts:
        response = runCommand(options.username, options.password, device, HOST_PORT, options.command)
        print "\nDevice: %s"%device
        if not ("error" in str(response).lower()):
            for output in response:
                print "Output from command:\n%s\n" %output
        else:
            print response



# End of Main function
if __name__ == "__main__":
    main()
