#!/usr/bin/env python
# Copyright (c) 2023, Arista Networks, Inc.
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
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# accessPort.py
#
#    Version 2.0 26/10/2023
#    Written by:
#       Hugh Adams, Arista Networks
#
#    Revision history:
#       1.0 - written using UNIX Sockets and pyeapi
#       2.0 - written using UNIX Sockets and jsonrpclib

"""
DESCRIPTION
    This script is designed to collect the MAC address or IP of a device plugged into a device port.
    The script will then assign the port to a given VLAN based on that MAC, IP, or hostname.

INSTALLATION
    In order to install this extension:
        - copy 'accessPort.py' to /mnt/flash
        - enable the Command API interface:
            management api http-commands
                protocol unix-socket
                no shutdown

    the accessPort.py can then be started using either:

    1 - Configure an event-handler on the switch for one interface:
        (config)# event-handler accessPort
                    trigger on-intf Ethernet10 operstatus
                    action bash
                        python3 /mnt/flash/accessPort.py
                        EOF
                    delay 15
                  exit

    2 - Configure an event-handler on the switch for multiple interfaces:
        (config)# event-handler accessPort
                    trigger on-intf Ethernet5-10,15-20 operstatus
                    action bash
                        python3 /mnt/flash/accessPort.py
                        EOF
                    delay 15
                  exit

COMPATIBILITY
    Version 1.0 has been developed and tested against vEOS-4.30.0F and is using the Command pyeapi.py.
 
    It should maintain backward compatibility with future EOS releases.
LIMITATIONS
    None known.
"""

# Imports
from jsonrpclib import Server

# Default Argument Values for user settings
scriptProtocol = 'local'

# Allowed Devices Attributes
deviceAttribs = {
    "ipList": {"192.168.60.5": 40, "192.168.65.10": 45, "192.168.30.103": 47},
    "macList": {"00:50:56:7a:03:01": 50, "50:d0:00:19:05:01": 55},
    "lldpList": {"uwdc-pc": 60}
}
# Dead End VLAN for in active ports
DEvlan = 999


# Main Function
def main():
    # Gather OS enviromental arguments
    intfStates = {}
    for env, intfName in os.environ.items():
        if env.startswith('INTF_'):
            intfStates[intfName] = os.environ['OPERSTATE_' + env[5:]]
        elif env.startswith('INTF'):
            intfStates[intfName] = os.environ['OPERSTATE']
    for interface in intfStates.keys():
        print("######\nWorking on %s" % interface)
# Reuquired Show commands
        command_IPaddr = "show ip arp interface %s" % interface
        command_MACaddr = "show mac address-table interface %s" % interface
        command_LLDP = "show lldp neighbors %s" % interface
        command_intStatus = "show interfaces %s status" % interface
# Required entities from show commands, default to empty lists in case of problems
        arpEntries = []
        macEntries = []
        lldpEntries = []
        intfDesc = ""
# Connect to switch and get show commands
        device = Server("unix:/var/run/command-api.sock")
        response = device.runCmds(1, [command_IPaddr, command_MACaddr, command_LLDP, command_intStatus], "json")
        #print(response)
        if len(response) > 0:
            errorFound = []
            if "error" not in response[3].keys():
                intfDesc = response[3].get("interfaceStatuses").get(interface).get("description")
            else:
                errorFound.append("IntfDesc - %S" % response[3]["error"])
            if "error" not in response[0].keys():
                arpEntries = response[0].get("ipV4Neighbors")
            else:
                errorFound.append("ARP Entries - %S" % response[0]["error"])
            if "error" not in response[1].keys():
                macEntries = response[1].get("unicastTable", {}).get("tableEntries")
            else:
                errorFound.append("MAC Entries - %S" % response[1]["error"])
            if "error" not in response[2].keys():
                lldpEntries = response[2].get("lldpNeighbors")
            else:
                errorFound.append("LLDP Entries - %S" % response[2]["error"])
            if len(errorFound) > 0:
                print("  Problem with fetching show commands:")
                for errorText in errorFound:
                    print("  "+str(errorText))
                exit(os.EX_PROTOCOL)
        else:
            print("  Problem with sending commands")
            exit(os.EX_PROTOCOL)

# Decide what actions are required
# set VLAN for moving device to, default deadend VLAN
        vlan = DEvlan
        matchFound = False
# Look for MAC addresses
        stop = False
        print("  Check in %s MAC entries for match" % len(macEntries))
        for macAddr in deviceAttribs["macList"].keys():
            for entry in macEntries:
                if macAddr in entry.get('macAddress'):
                    print("    Found MAC Address: %s\n" % macAddr)
                    vlan = deviceAttribs["macList"][macAddr]
                    stop = True
                    break
            if stop:
                matchFound = True
                break
# Look for IP addresses
        stop = False
        print("  Check in %s IP address for match" % len(arpEntries))
        for ipAddr in deviceAttribs["ipList"].keys():
            for entry in arpEntries:
                if ipAddr in entry.get('address'):
                    print("    Found IP Address %s\n" % ipAddr)
                    vlan = deviceAttribs["ipList"][ipAddr]
                    stop = True
                    break
            if stop:
                matchFound = True
                break
# Look for LLDP Neighbor
        stop = False
        print("  Check in %s LLDP neighbors for match" % len(lldpEntries))
        for lldpNeighbor in deviceAttribs["lldpList"].keys():
            for entry in lldpEntries:
                if lldpNeighbor in entry.get("neighborDevice"):
                    print("    Found LLDP Neighbor %s\n" % lldpNeighbor)
                    vlan = deviceAttribs["lldpList"][lldpNeighbor]
                    stop = True
                    break
            if stop:
                matchFound = True
                break
# Configure the switch
        if matchFound:
            print("  Interface %s Matches found, configuration will be changed" % interface)
        else:
            print("  NO matches found Interface % s, configuration will only be changed if link status is 'down'"% interface)
            print("  If link status is up vlan will be set to default VLAN%s" % vlan)
# Required Configuration Commands
        confChanged = False
# Assign port to required VLAN from deviceAttribs if not configured before and link state is up
        if "port_active" not in intfDesc and "linkup" in intfStates[interface]:
            response = device.runCmds(1, ["enable", "configure", "interface %s" % interface, "switchport access vlan %s" % vlan, "description port_active", "exit"])
            confChanged = True
# Assign port to VLAN 999 if not configured before and link state is up
        if "port_active" in intfDesc and "linkdown" in intfStates[interface]:
            vlan = DEvlan
            response = device.runCmds(1, ["enable", "configure", "interface %s" %interface, "switchport access vlan %s" % vlan, "description port_inactive", "exit"])
            confChanged = True
# Check Configuration
        if confChanged:
            configOK = True
            for item in response:
                if "error" in item.keys():
                    configOK = False
                    print("  Interface %s - Configuration Error:%s" %(interface, item["error"]))
            if configOK:
                print("  Interface %s - Configured successfully with %s" %(interface, vlan))
        else:
            print("  Interface %s - No change in config" % interface)

if __name__ == "__main__":
    main()
