# DataConfigletBuilder

**Objective**

This script creates a CVP Configlet and stores JSON (Java Script Object Notation) formatted data in it. The data is generated from the contents of the Excel Spreadsheet Demo_Data. The Spreadsheet provides the base device information such as hostname and management IP address in the BASECONFIG tab along with some site specific Global Variables in the GLOBAL tab. The CONFIGLETS_DC1-PRD provides a patching schedule that describes how all of the interfaces in the Demo are connected.

**Dependencies**

The script has dependencies on the following python libraries:
 - xlrd
 - xlwt
 - netaddr
 - json
 - re
 - collections
 - os
 - argparse
 - getpass
 - sys
 - requests
 - time

**Command Line Options**

optional arguments:
  -h, --help                            show help message and exit
  --userName {{username}}               Username to log into CVP
  --password {{Password}}               Password for CVP user to login
  --target   {{CVP IP address or URL}}  CVP appliance to create Data Configlet on
  --configlet {{Configlet NAme}}        CVP Configlet to contain data
  --xlfile {{Excel filename}}           Excel file (.xls) containing data (Demo_data.xls
                                        in this example)
  --jsonfile {{JSON Data File}}         Existing file (.json) containing JSON data from
                                        spreadsheet
  --test {{'Y' or 'N'}}                 Testing do not upload data to CVP
  --verbose {{'Y' or 'N'}}              Enable Verbose Output
