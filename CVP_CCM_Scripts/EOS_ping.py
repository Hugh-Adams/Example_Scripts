# Copyright (c) 2022, Arista Networks
# All rights reserved.
#
import re
# Create Script variables
scriptArgs = ctx.changeControl.args
scriptArgs['targetList']=re.split(',',scriptArgs['targetList'])

# Internal Variables
passed = 0
failed = 0

# Write entry to Log
ctx.alog("device_ping - checking endpoint connectivity")
device_ip = ctx.getDevice().ip
# Start ping tests from context devices
ctx.alog("device_ping: Connecting to %s" %device_ip)
for target in scriptArgs['targetList']:
    tempOutput = ctx.runDeviceCmds(["enable", "cli vrf %s" % scriptArgs['vrf'], "ping %s" % target])
    output = tempOutput[2]["response"]["messages"][0].splitlines()
    # Extract Ping results
    if "statistics" in str(output):
        ping_stats = re.split(',', output[-2])
        ping_tx = re.split('(\d+)',ping_stats[0])[1]
        ping_rx = re.split('(\d+)',ping_stats[1])[1]
        ping_pkl = re.split('(\d+)',ping_stats[2])[1]
        ping_pkr = 100-int(ping_pkl)
    else:
        ping_pkr = "0"
        ctx.alog("device_ping: Ping form %s to %s ERROR: %s" %(device_ip, target, output))
    # Check Ping Results and Log them
    if int(ping_pkr) >= int(scriptArgs['passmark']):
        ctx.alog("device_ping: Ping form %s to %s - Pass" %(device_ip, target))
        passed += 1
    else:
        ctx.alog("device_ping: Ping form %s to %s - Failed" %(device_ip, target))
        failed += 1
# If number of Ping tests that failed exceeds failCount
# fail the whole test
if int(scriptArgs['failCount']) > failed:
    ctx.alog("device_ping: Passed - Number of failures must be less than %s.\n%s device(s) recieved the required number of pings" %(scriptArgs['failCount'],passed))
else:
    ctx.alog("device_ping: - Failed Number of failures must be less than %s.\n%s device(s) did not recieve the required number of pings" %(scriptArgs['failCount'],failed))
    raise UserWarning("device_ping: Failed")


# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#   Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
#   Neither the name of Arista Networks nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# 'AS IS' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ARISTA NETWORKS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
