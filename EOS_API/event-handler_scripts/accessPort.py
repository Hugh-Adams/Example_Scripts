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
#    Version 1.0 10/10/2023
#    Written by:
#       Hugh Adams, Arista Networks
#
#    Revision history:
#       1.0 - initially written using UNIX Sockets


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
                        python /mnt/flash/accessPort.py
                        EOF
                    delay 2
                  exit

    2 - Configure an event-handler on the switch for multiple interfaces:
        (config)# event-handler accessPort
                    trigger on-intf Ethernet5-10,15-20 operstatus
                    action bash
                        python /mnt/flash/accessPort.py
                        EOF
                    delay 2
                  exit

COMPATIBILITY
    Version 1.0 has been developed and tested against vEOS-4.30.0F and is using the Command pyeapi.py. 
    It should maintain backward compatibility with future EOS releases.
LIMITATIONS
    None known.
"""

# Imports
import os,sys
import pyeapi
import ssl

# Default Argument Values for user settings
scriptProtocol = 'local'

# Allowed Devices Attributes
deviceAttribs = {
    "ipList": {"192.168.60.5": 40, "192.168.65.10": 45, "192.168.30.101": 47},
    "macList": {"00:50:56:7a:03:01": 50, "50:d0:00:18:05:00": 55},
    "lldpList": {"UWDC-LEAF-021": 60 }
}
# Dead End VLAN for in active ports
DEvlan = 999

class Device(object):
    """ Function to connect to EAPI interface on a switch and send commands to it, the routine will return
    the output of each command in JSON format by default.
        user     - username to access switch with, requires correct privledge level to run the required commands
        passwd   - password for above user
        address  - ip or url for target switch
        protocol - protocol to use for EAPI session https, or local (unix sockets)
        commands - list of commands to pass to the switch
    """

    def __init__(self, address='127.0.0.1', user='', passwd='', protocol="local"):
        # Ignore any invalid cert warnings
        ssl._create_default_https_context = ssl._create_unverified_context

        if protocol == "https":
            self.portNo = "443"
            #Connect to Switch via HTTPS eAPI
            self.switch = pyeapi.connect(host=address, username=user, password=passwd, port=self.portNo)
        elif protocol == "local":
            # Connect to Switch via Unix Socket
            self.switch = pyeapi.connect(transport='socket')
        else:
            print("Problem connecting to device: unrecognised protocol")

    def runCmds(self, commands):
        """ send commands to switch it return the output of each command in JSON format by default.
            commands - list of commands to pass to the switch
        """

        # capture Connection problem messages:
        self.response = self.switch.execute(commands)
        return self.response['result']

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
# Reuquired Show commands
        command_IPaddr = "show ip arp interface %s" %interface
        command_MACaddr = "show mac address-table interface %s" %interface
        command_LLDP = "show lldp neighbors %s" %interface
        command_intStatus = "show interfaces %s status"%interface
# Required entities from show commands, default to empty lists in case of problems
        arpEntries = []
        macEntries = []
        lldpEntries = []
        intfDesc = ""
# Connect to switch and get show commands
        device = Device(protocol=scriptProtocol)
        response = device.runCmds([command_IPaddr,command_MACaddr,command_LLDP,command_intStatus])
        #print(response)
        if "error" not in response[3].keys():
            intfDesc = response[3].get("interfaceStatuses").get(interface).get("description")
            if "error" not in response[0].keys():
                arpEntries = response[0].get("ipV4Neighbors")
                if "error" not in response[1].keys():
                    macEntries = response[1].get("unicastTable",{}).get("tableEntries")
                    if "error" not in response[2].keys():
                        lldpEntries = response[2].get("lldpNeighbors")           
        else:
            print ("Problem with fetching show commands")
            exit(os.EX_PROTOCOL)
# Decide what actions are required
# set VLAN for moving device to, default deadend VLAN
        vlan = DEvlan
# Look for MAC addresses
        stop = False
        for macAddr in deviceAttribs["macList"].keys():
            for entry in macEntries:
                print("  Checking %s" %macAddr)
                if macAddr in entry.get('macAddress'):
                    print("  Found MAC Address\n")
                    vlan = deviceAttribs["macList"][macAddr]
                    stop = True
                    break
            if stop:
                break
# Look for IP addresses
        stop = False
        for ipAddr in deviceAttribs["ipList"].keys():
            for entry in arpEntries:
                print("  Checking %s" % ipAddr)
                if ipAddr in entry.get('address'):
                    print("  Found IP Address\n")
                    vlan = deviceAttribs["ipList"][ipAddr]
                    stop = True
                    break
            if stop:
                break
# Look for LLDP Neighbor
        stop = False
        for lldpNeighbor in deviceAttribs["lldpList"].keys():
            for entry in lldpEntries:
                print("  Checking %s" %lldpNeighbor)
                if lldpNeighbor in entry.get("neighborDevice"):
                    print("  Found LLDP Neighbor\n")
                    vlan = deviceAttribs["lldpList"][lldpNeighbor]
                    stop = True
                    break
            if stop:
                break
# Configure the switch
# Required Configuration Commands
        confChanged = False
# Assign port to required VLAN from deviceAttribs if not configured before and link state is up
        if "port_active" not in intfDesc and "linkup" in intfStates[interface]:
            response = device.runCmds(["enable", "configure", "interface %s" % interface,
                                    "switchport access vlan %s" %vlan, "description port_active", "exit"])
            confChanged = True
# Assign port to VLAN 999 if not configured before and link state is up
        if "port_active" in intfDesc and "linkdown" in intfStates[interface]:
            vlan = DEvlan
            confChanged = True
            response = device.runCmds(["enable", "configure", "interface %s" %
                                    interface, "switchport access vlan %s"%vlan, "description port_inactive", "exit"])

# Check Configuration
        if confChanged:
            configOK = True
            for item in response:
                if "error" in item.keys():
                    configOK = False
                    print("Interface %s - Configuration Error:%s"%(interface,item["error"]))
            if configOK:
                print("  Interface %s - Configured successfully with %s"%(interface,vlan))
        else:
            print("  Interface %s - No change in config"%interface)


if __name__ == "__main__":
    main()
