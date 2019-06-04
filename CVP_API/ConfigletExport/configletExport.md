# Configlet Export

**Objective**

This script creates a CVP Configlet export (Static Configlets, ConfigletBuilders,and/or Generated Configlets) and transfers it to a server for backup and recovery purposes

**Dependencies**

The script has dependencies on the following python libraries:
 - sys
 - os
 - getpass
 - argparse
 - requests
 - json
 - paramiko
 - scp
 - time


**Command Line Options**

- host {{host}}	can be localhost if script is running on CVP or FQDN or IP of CVP server if remote.

- user {{username}}	CVP user with rights to execute a Configlet export see below.

- password {{password}}	password for CVP user

- configlets {{configletList}}	optional list of Configlets to export from CVP, default is all

- Ctype {{configletType}}	optional Type of Configlet to export:
    Configlet – Configlets
    Static – Configlets created manually
    Builder – Configlet Builders
    Generated – Configlets created by Configlet Builders
    All – all of the above
  Default Ctype is All

- copyHost {{hostIP/FQDN}}	URL or IP of host to copy export file to

- copyUser {{userName}}	username to access copy host.

- copyPassword {{password}}	password for user to access copy host

- destPath	directory in which to copy exported Configlets file.
            “/data/backup/arista/configlets/ ” for example

- xferOption	optional selection of SCP or SFTP file transfer to copy host. Defaults to SFTP
