# CVP_API

These scripts use the requests library to make RESTful API calls to CVP to achieve various tasks.
Care should be taken with these scripts as the API calls may not work with CVP versions beyond 2018.1.4 unless otherwise stated.

**Audit_Report**

Provides a means to audit multiple instances of CVP to ensure that configurations and container structures have been created and assigned correctly. The reports help identify configuration creep in both CVP and the devices.

**Backup_and_Transfer**

This script can be used either locally on the CVP appliance or from a remote server to automate the creation of a regular CVP back and transfer the backup file to a host for inclusion in an enterprise backup schedule. The script avoids the need to install any third party backup agents on the CVP appliances

**ConfigletExport**

Quick way to create a CVP Configlet export (Static Configlets, ConfigletBuilders,and/or Generated Configlets) and transfer it to a server for backup and recovery purposes

**Configlet Search**

This script searches the available Configlets in CVP for a user defined string and returns the Configlets that have matches for it.

**Password change**

This script allows the user to change and encrypt passwords inside a Configlet.

**Reconcile Configlet Name change**

The script allows the user to change the name of the reconcile Configlets after they have been provisioned without resetting the reconcile flag in the Configlet metadata.

**DataConfigletBuilder**

This script creates a CVP Configlet and stores JSON (Java Script Object Notation) formatted data in it. The data is generated from the contents of the Excel Spreadsheet Demo_Data.

**Snapshot Utils**

These scripts provide methods for the user to retrieve CloudVision Snapshots and save them to a local file space.
