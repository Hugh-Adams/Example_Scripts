#DeviceConfiglet Configlet Builder

**Objective**

This Configlet Builder utilises the Data Configlet generated using the DataConfigletBuilder script in the CVP_API collection. The Data from the Configlet is combined with the Jinja2 Templates stored in the accompanying Configlets to produce device specific Configlets that are attached to the Target device.

**Dependencies**

The script has dependencies on the following python libraries:
 - cvplibrary
 - json
 - re
 - jinja2
 - ssl

**Menu Options**

Device {{Device Name or System MAC address}}
 used to select device to build Configlets for. If "CVP-select" is entered the value from the "Devices" drop down box will be used. This is the default option allowing the script to be used in the provisioning view. If "ALL" is entered configlets for all devices defined in the JSON data will be built.

Location ID {{Three Letter Site ID}}
 In the example the switches use a three letter site identifier as part of their hostname, the Configlet builder uses this to filter switches in a particular site and only build Configlets for them. The site IDs have to match those in the JSON data.

Template {{tick box selection}}
  - default builds a device Configlet based on a predefined default template coded into the script.
  - ALL builds all configlets defined in the JSON data
  - base-sw builds the base config (hostname, management IP, management API interface) for a device
  - nw builds infrastructure links and routing config. This is the core network configuration upon which all else is built.
  - gw builds a Configlet used to provide interface and BGP configuration for connection to other 3rd party networks
  - fw builds a Configlet used to provide interface and BGP configuration for connection to layer 3 firewalls
  - ep builds a configlet to provide connectivity to end points such as servers.
  - spine creates a configlet for provisoning spine devices
