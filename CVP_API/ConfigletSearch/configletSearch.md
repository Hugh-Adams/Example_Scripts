# Configlet Search

**Objective**

This script searches the available configlets in CVP for a user defined string and returns the configlets that have matches for it in them.

**Dependencies**

The script has dependencies on the following python libraries:
 - argparse
 - getpass
 - re
 - json
 - requests
 - os
 - csv
 - sys


**Command Line Options**

- host {{hostname or IP}} - Hostname or IP address of the CVP appliance

- user {{username}} - CVP user username to access the appliance

- password {{password}} - password corresponding to the CVP username

- Ctype {{configlet type}} - default:All - Type of Configlet to search, options are Static, Builder, Generated, or All

- search {{search string}} - Text string to match in Configlet

- retrieve {{True/False}} - default:False - Option to save matching Configlet options are True(Display and save the Configlet) or False(display Configlet only)
