#Backup and Transfer

**Objective**

This script creates a CVP backup, once complete it then transfers the backup zip file off the CVP appliance to a backup server. To complete its task the script then tidies up the backs retaining the ‘n’ backups where ‘n’ is user defined.

**Dependencies**

The script has dependencies on the following python libraries:
 - scp
 - paramiko
 - argparse
 - requests

**Command Line Options**

The script has the following command line options to complete:

- userName {{cvpUserName}} username for CVP appliance

- password {{cvpPassWord}} password for CVP user

- target {{cvpServer/appliance}} option for remote appliance, for on appliance crontab use “localhost”

- destHost {{ftpServerAddress}} server to send completed backup file to

- backupUser {{ftpServerUser}} username to access the designated backup server

- backupPassword {{ftpServerPassword}} password for server user

- destPath {ftpServerFilePath}} directory to copy backup file to on server: “/data/backup/arista/backup/” for example

- xferOption select SCP or SFTP file transfer, default is SFTP.  option NONE causes the script to create the backup but not copy it anywhere, this option is used mainly for testing.

- limit  number of Backups to keep on the CVP server. Default = 10, a value of 0 will keep all backups. 
