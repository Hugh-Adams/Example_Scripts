#Management Interface Configlet Builder

**Objective**

This Configlet Builder provides a simple example of how to automatically create the management interface for each switch as it is added to CVP. This prevents CVP from losing management contact with the switch. The builder retrieves the IP address from CVP then get the CIDR mask length and hostname from the switch itself.

**Dependencies**

The script has dependencies on the following python libraries:
 - cvplibrary
