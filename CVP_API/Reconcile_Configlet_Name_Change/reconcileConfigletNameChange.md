#Reconcile Configlet Name change

**Objective**

The script allows the user to change the name of the reconcile Configlets after they have been provisioned without resetting the reconcile flag in the Configlet metadata. This provides a way to change the Configlet name from “RECONCILE_{{IPaddress}}” to “RECONCILE_{{hostName}}. Provide as part of a demo of the CVP API.

**Dependencies**

The script has dependencies on the following python libraries:
 - getpass
 - argparse
 - json
 - requests

**Command Line Options**

The script has the following command line options to complete:

- host{{host}} URL of CVP appliance to connect to ( FQDN or IP of CVP server).

- user{{username}} CVP user with rights to execute a snapshot fetch see below.

- password{{password}} Password for CVP user
