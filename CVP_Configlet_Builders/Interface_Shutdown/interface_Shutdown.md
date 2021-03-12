#Interface_Shutdown Configlet Builder

**Objective**

This Configlet Builder amends a target configlet with a set of interface configurations that will shutdown any unused interface.
The script does this by parsing the physical switch interfaces and checking for a description.
If the interface has a description it is assumed to be configured if not it will be shutdown.

**Dependencies**

The script has dependencies on the following python libraries:
 - cvplibrary
 - json
 - os
 - re
 - ssl

**Menu Options**

Select if running in Provisioning Hierarchy or Automatic update - default Hierarchy {{automatic}}
If automatic is selected then all provisioned switches in the CloudVision inventory that are not in the "Undefined" container
will have their interfaces checked and updated.
If automatic is not selected then the target device will be selected either through the provisioning process or from the "Device" drop down if 
the script is being used in the configlet edit mode
