# CloudVision 202X Configlet Sync

## Objective
Synchronize Configlets between two CVP servers.


## Dependencies
The scripts have dependencies on the following python libraries:

 - json
 - requests
 - os
 - sys
 - argparse
 - tqdm

## Scripts and Options
### CV-202x_configletSync.py

**description:**
Synchronize Configlets between two CVP servers.
Backups are stored in local sub directories named after the CVP server they are from

**options:**

`-s --srcServer`  Source CloudVision server, e.g 10.83.12.79 or CV.lab.arista.com
`-d --destServer` Destination CloudVision server, e.g  e.g 10.83.12.79 or CV.lab.arista.com
`-u --user`       CloudVision User Name
`-p --passwd`     User's Password
`-f --filter`     Configlet Filter (lazy match) .Only select Configlets that match filter
`-o --overwrite` Overwrite destination CVP Server configlets with source CVP Server configlets, default action is to Sync to latest Configlet
`-a --add`       Add missing configlets form source CVP Server to destination CVP Server that are not present on the destination CVP

