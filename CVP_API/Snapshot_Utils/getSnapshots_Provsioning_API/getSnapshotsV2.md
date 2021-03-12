# GetSnapshots

**Objective**

This script can be used to retrieve the custom cli outputs from a set of Snapshots. The outputs are retrieved as text files and JSON files. The script has been used to gather “show running configuration” and “show tech support” information for use with PS/AS reports and for TAC cases. It has also been used to provide reports for daily Operational checks.

**Dependencies**

The script has dependencies on the following python libraries:
 - sys
 - getpass
 - argparse
 - requests

**Command Line Options**

The script has the following command line options to complete:

- target {{host}}	List of CVP appliances to connect to ( FQDN or IP of CVP servers).
- userName {{username}}	CVP user with rights to execute a snapshot fetch see below.
- password {{password}}	Password for CVP user
- destPath {{directoryPath}}	Directory to download snapshot files to.
- snapshot {{snapshotName}}	Name of CVP snapshot to retrieve data for..
