#VariableDiscovery

**Objective**

This Studio is provided to help understand the Studio context variables available in a Studio template. The Studio does not produce any configuration that can be applied to a device its output consists of comments.

**Studio Options**

Debug {{Boolean Toggle}}
 provided to create a change in the input data to generate an output configuration.

 **Studio Operations**

 Start the Studio in a new or existing workspace, toggle the debug option and select the Review Workspace to update the Studio in the workspace. To generate the output select the Start Build this will produce a config that can be reviewed in the "View Build Details".The config associated with the target device will now contain a set of comments starting with "!" that reveal the available context (ctx) variables for the Studio.
