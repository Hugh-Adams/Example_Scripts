#!/usr/bin/env python
#
# Copyright (c) 2018, Arista Networks, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#  - Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#  - Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#  - Neither the name of Arista Networks nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

# Import Required Libraries

import re
import argparse

def asnCalc(asn):
    """ calculate both types of ASN plain and dotted fron ASN value
        if the ASN has a dot in it assume as-asdot otherwise as-asplain
        return both types asn-asdot followed by asn-asplain"""
    if "." in str(asn):
        asnSplit= re.split('\.',str(asn))
        asdot=str(asn)
        asplain = str((int(asnSplit[0])*65536)+int(asnSplit[1]))
    else:
        asDot_Top = str(int(float(asn)//65536))
        asDot_Btm = str(int(float(asn)%65536))
        asDot_Btm = asDot_Btm.rjust(5, '0')
        asdot = asDot_Top+"."+asDot_Btm
        asplain = str(asn)
    return [asdot,asplain]
                      
def parseArgs():
    """Calculate AS Numbers  from AS-DOT or AS-PLAIN"""
    # Configure the option parser for CLI options to the script
    usage = "usage: %prog [options] BGP AS Number"
    parser = argparse.ArgumentParser(description="Calculate BGP AS Numbers")
    parser.add_argument("ASN", type=str, help='Enter BGP AS Number ASdot or ASplain')
    args = parser.parse_args()
    return args

# Main Script
def main():
    # Set Intial Variables required
    options = parseArgs()
    ASNreturn = asnCalc(options.ASN)
    print "BGP AS Number\nAS-DOT - %s\nAS-PLAIN - %s" %(ASNreturn[0],ASNreturn[1])
        
if __name__ == '__main__':
    main()
