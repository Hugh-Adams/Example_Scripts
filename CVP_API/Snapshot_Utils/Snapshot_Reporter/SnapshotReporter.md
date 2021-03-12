# Snapshot Reporter

**Objective**

This script searches the available Snapshots and returns the last snapshot for each device that matches the snapshot name provided.

**Dependencies**

The script has dependencies on the following python libraries:

 - json
 - re
 - os
 - csv
 - argparse
 - getpass
 - sys
 - json
 - requests
 - time

**Command Line Options**

- userName {{username}} - Username to log into CVP

- password {{password}} - Password for CVP user to login

- target {{list of URLS or IP addresses}} - List of CVP appliances to get snapshot from comma Separated

- snapshot {{snapshot name}} - CVP Snapshot containing required data

- last {{True/False}} default:True - True - Only get latest snapshot for each device or False - Get all snapshots for each device
