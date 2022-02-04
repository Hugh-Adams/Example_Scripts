#SimpleServiceInterface

**Objective**

This Studio is provided in order to demonstrate a simple method of creating VLAN trunked interfaces on devices. The VLANs in this example represent access to a different service. An interface can be configured as a VLAN trunk containing multiple VLANs. The VLANs can be defined/associated with different service names.

**Studio Options**

Device {{Device Object List}}
 Add devices to the list to assign their interface Service VLANs. The Devices are affected by the Tag Assignments at the top of the studio.

 Interface Profiles {{Service name and VLAN list}}
  Add service names to be provided on the Trunk Interfaces and their associated VLANs.

 **Studio Operations**

 Start the Studio in a new or existing workspace, define any required Interface Profiles required (minimum of 1).
 Add or select a device to be configured.
 Select the required interface to be configured.
 Add or Remove the required Service names.
 When the Studio updates are complete select the "Review Workspace" to submit it and then select "Start Build" to generate the configuration.
