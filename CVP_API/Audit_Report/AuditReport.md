#Backup and Transfer

**Objective**
The Audit Report provides concise CSV outputs that audit the structure of the configuration generated, along with associated Software Images applied and final device configurations. These reports provide a simple way to audit CVP installations and compare multiple CVP installations across different sites

Three reports can be produced:
    DeviceReport - CSV matrix of Devices and the Configlets applied to them
    ConfigletReport - CSV matrix of Configlets, Configlet Type (Static, Builder)
                      Container Applied to, and devices affected by it
    Configlet Diffs - Comparison of similar Configlets across multiple CVP instances,
                      used to check consistence of applied configuration. Report
                      includes a caparison score (100 - identical, 0 - very different)
                      and a separate diff file (html) highlighting the differences
    The reports will be saved to the same directory location as the script

**Dependencies**

The script has dependencies on the following python libraries:
 - re
 - os
 - csv
 - argparse
 - getpass
 - sys
 - json
 - requests
 - time
 - difflib
 - fuzzywuzzy

**Command Line Options**

- username {{username}} CloudVision Portal user name to login with, if accessing multiple instances of CVP the username must be available in each instance

- password {{password}} Password for user specified in username if accessing multiple instances of CVP the password must be the same in each instance

- target {{list of CVP appliances}} List of CVP appliances to create reports for, the primary node in
                  each cluster should be provided. Each URL or IP address separated by a comma.

- configlet {{list of Configlet name filters}} List of name filters to use to match (include) Configlets in the audit report. Assuming a standard naming convention this list can be used to filter out device specific Configlets as these are likely to different for each device making any diff report with them in pointless.

- option {{reports to create}} List of reports to create, each report option separated by a comma.
    options:
    - all - ouptut all available reports
    - configlet - output Configlet assignments 1 report per CVP appliance includes Configlet associations and final device configurations
    - configuration - output comparison of similar Configlets across CVP appliances
    - devices - output of device inventory type data

- diffRatio {{number 0 - 100}} Comparison threshold used to decide if two Configlets are similar
                  enough to be the same. A ratio of 100 would mean that both Configlets would have to be identical. A ratio of 90 generally gives a good comparison result.
