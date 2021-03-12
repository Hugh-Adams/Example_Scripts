# CVP_Configlet_Builders

These Configlet Builders provide some simple examples of operational tasks that can be performed in CVP using the scripting capabilities provided by the Configlet Builders.

**My_First**

This Configlet Builder provides a simple example of how to combine the Configlet builder menu options with a simple python script to create a basic interface configuration. To use the script import the zip into CVP in the "Configlets" page, then open the newly imported ConfigletBuilder.

**PasswordChange**

This Configlet Builder allows the user to change and encrypt passwords inside a Configlet. The Builder was originally developed to assist Operational teams change the local user password for admin and cvpadmin on their switches using CVP. The builder menu has the option to add two additional users into the Configlets and define custom user roles. The builder also uses the menu item dependency option to only reveal menu fields that are required for specific users.

**SimpleInterface**

This Configlet Builder provides a simple example of how to use the Form Builder and a short python script to create a basic interface configuration.

**SimpleServiceInterface**

This Configlet Builder demonstrates the use of Form Builder Tick boxes to create interfaces with predefined configuration based on which services are to be supplied to the subscriber. Each service is provided on a different VLAN in this example.

**Management Interface**

This Configlet Builder provides a simple example of how to automatically create the management interface for each switch as it is added to CVP. This prevents CVP from losing management contact with the switch.

**DeviceConfiglet Configlet Builder**

This Configlet Builder utilises the Data Configlet generated using the DataConfigletBuilder script in the CVP_API collection. The Data from the Configlet is combined with the Jinja2 Templates stored in the accompanying Configlets to produce device specific Configlets that are attached to the Target device.
