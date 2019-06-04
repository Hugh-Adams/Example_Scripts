#PasswordChange

**Objective**

This script allows the user to change and encrypt passwords inside a Configlet. The script was originally developed to assist Operational teams change the local user password for admin and cvpadmin on their switches using CVP. The script ensures that passwords are never written in plain text at anytime during the process. The cvpdamin password is the exception as this has to be updated manually through the GUI.

**Dependencies**

The script has dependencies on the following python libraries:
 - getpass
 - argparse
 - json
 - requests
 - passlib

**Command Line Options**
The script has the following command line options to complete:

- appList{{host(s)}} List of CVP appliances to connect to ( FQDN or IP of CVP servers).

- userName{{username}} CVP user with rights to execute a snapshot fetch see below.

- password{{password}} Password for CVP user

- configlet{{configletName}} Name of CVP configlet that contains the device local users
