# Snapshot Utils

**Snapshot Reporter**

This script searches the available Snapshots and returns the last snapshot for each device that matches the snapshot name provided.

**getSnapshots_Provisioning_API**

This script can be used to retrieve the custom cli outputs from a set of Snapshots. The outputs are retrieved as text files and JSON files. The script has been used to gather “show running configuration” and “show tech support” information for use with PS/AS reports and for TAC cases. It has also been used to provide reports for daily Operational checks.

This script works with CloudVision Versions 201x.x and below

**getSnapshots_Resource_API**

These script can be used to retrieve the custom cli outputs from a set of Snapshots. The outputs are retrieved as text files and JSON files. The script has been used to gather “show running configuration” and “show tech support” information for use with PS/AS reports and for TAC cases. It has also been used to provide reports for daily Operational checks.

These script work with CloudVision Versions 202x.x and above utilizing the Resources gRPC API, the script requires the use of the CloudVision Certificates and Tokens.

**OpticDataRetriever**

This script re-uses the getSnapshot scripts to retrieve snapshots with the show inventory commands in and then filters the snapshot output to produce a lists of Optical transceivers of a given type and their serial numbers.

This script works with CloudVision Versions 201x.x and below