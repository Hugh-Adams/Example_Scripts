
#!/usr/bin/env python
"""
DESCRIPTION
    This script is designed to test an Interface event handler and display
    the status of the interfaces included in the event handler configuration.

INSTALLATION
   In order to install this extension:
      - copy 'INTF_event-handler_test.py' to /mnt/flash on the test switch
      - enable the Command API interface:
         management api http-commands
            protocol unix-socket
            no shutdown

   The script can then be started using any of the following methods:

   Configure an event-handler on the switch:
      (config)# event-handler INTF_Test
                  trigger on-intf Ethernet10 operstatus
                  action bash
                     python /mnt/flash/INTF_event-handler_test.py
                     EOF
                  delay 2
               exit
      (config)# event-handler INTFs_Test
                  trigger on-intf Ethernet10-15 operstatus
                  action bash
                     python /mnt/flash/INTF_event-handler_test.py
                     EOF
                  delay 2
               exit
   Change the state of one or more of the interface specidied in the trigger
   To view the output of the script use the follwing command
      # more file:/var/log/event/INTF_Test
      or
      # more file:/var/log/event/INTFs_Test
   where INTF_Test is the name of the event handler.

COMPATIBILITY
    Version 1.0 has been developed and tested against vEOS-4.30.0F. 
    It should maintain backward compatibility with future EOS releases.
LIMITATIONS
    None known.
"""
import os
for env, intfName in os.environ.items():
   if env.startswith( 'INTF_' ):
      print ("%s : %s" %( intfName, os.environ[ 'OPERSTATE_' + env[5:]]))
   elif env.startswith('INTF'):
      print ("%s : %s"%(intfName,os.environ['OPERSTATE']))