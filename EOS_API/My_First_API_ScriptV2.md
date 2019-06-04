#Backup and Transfer

**Objective**
Example EOS API script that runs a set of commands on a set of switches and returns the JSON formatted results. 

**Dependencies**

The script has dependencies on the following python libraries:

 - argparse
 - getpass
 - sys
 - ssl
 - socket
 - errno
 - json
 - re
 - jsonrpclib

**Command Line Options**

- username {{username}} default: admin - Username to access switches with
  Remove default option to get user prompt for this CLI input

- password {{password}} default: arista - Password for user to access switches
  Remove default option to get user prompt for this CLI input

- hosts  {{list of switches}} - Switch IP addresses or URLs separated with a comma
  to run command(s) on.

- command {{list of commands}} - Commands to execute through API separated with a comma
