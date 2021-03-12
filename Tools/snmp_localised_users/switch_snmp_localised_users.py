#!/usr/bin/env python
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
import uuid
import hashlib

def eosEngineID(dev_mac):
  """
    Return the SNMP Engine ID generated from the System MAC
    this is the version used in EOS
  """
  return "f5717f" + str(dev_mac).replace(":", "") + "00"

def genEngineID ():
    """genEngineID - generates an SNMP EngineID for Arista devices
    using a random uuid.  This is different than the method used
    when configuring via the cli, so any users generated using this
    engineID will be incompatible with any added from the cli."""

    # Arista's PEN, with the high bit set: "\x80\x00\x75\x71"
    # Type 5: "Administratively assigned octets": "\x05"
    engineId = bytearray.fromhex('8000757105')
    print ("Engine ID prefix {}" .format(engineId.hex()))
    # Add a random (type 4) UUID:
    engineUuid = uuid.uuid4().bytes
    engineId += engineUuid
    print ("Engine UUID {}".format(engineUuid.hex()))
    print ("Engine ID {}".format(engineId.hex()))
    return engineId

def get_hasher(authType):
  """
    Return the required hash function based
    on the authentication type required
  """
  if authType == 'md5':
      hasher = hashlib.md5
  elif authType == 'sha':
      hasher = hashlib.sha1
  elif authType == 'sha224':
      hasher = hashlib.sha224
  elif authType == 'sha256':
      hasher = hashlib.sha256
  elif authType == 'sha384':
      hasher = hashlib.sha384
  elif authType == 'sha512':
      hasher = hashlib.sha512
  else:
      hasher = None
  return hasher


def keyFromPassphrase(phrase, authType):
  """
    Generates a key from a passphrase as describe in RFC 2574 section A.2.
    authType should be 'md5', 'sha', or 'sha(224|256|384|512)'.
  """
  # Commented out lines - Python 2
  hasher = get_hasher(authType)
  hashVal = hasher()
  bytesLeft = 1048576  # 1Megabyte
  #concat = phrase
  concat = phrase.encode('utf-8')
  # Concatenate phrase until its at least 64 characters long
  while len(concat) < 64:
      #concat += phrase
      concat += phrase.encode('utf-8')
  concatLen = len(concat)
  # Hash the new Concatenated phrase until its 1Mb in length
  while bytesLeft > concatLen:
      hashVal.update(concat)
      bytesLeft -= concatLen
  if bytesLeft > 0:
      hashVal.update(concat[0: bytesLeft])
  # Create the hexadecimal value for the hashed phrase
  #ku = hashVal.hexdigest()
  ku = hashVal.digest()
  return ku


def localizePassphrase(phrase, authType, engineID, privType):
  """
    Performs a key localization as described in RFC 2574 section 2.6.
    phrase is the plain ASCII passphrase. 
    [authType] - 'md5', 'sha', or 'sha(224|256|384|512)'.
    [engineId] - *binary* value of the engineID.
      (Not "8000757105..." but "\x80\x00\x75\x71\x05...")
    [privType] - privacy protocol, 'des', 'aes', 'aes192' or 'aes256'
      This is needed when we need to create a longer Localized Key (kul)
      for a stronger privacy protocol.
  """
  engineId = bytearray.fromhex(engineID)
  # Create Standard User Key Ku from phrase
  #ku = keyFromPassphrase(phrase, authType).decode("hex")
  ku = keyFromPassphrase(phrase, authType)
  hasher = get_hasher(authType)
  localHash = hasher()
  # Localize the Standard Key by adding the local engineID to it
  # Localized key - kul
  localHash.update(ku + engineId + ku)
  #kul = localHash.hexdigest()
  kul = localHash.digest()
  #kulHash = localHash.hexdigest()
  kulHash = localHash.digest()
  # Defined Number of Characters required for each hash type as used in EOS
  reqLenMap = {'md5': 32, 'sha': 40,
               'sha224': 56, 'sha256': 64,
               'sha384': 96, 'sha512': 128,
               'des': 32, 'aes': 32,
               'aes192': 48, 'aes256': 64}
  authLen = reqLenMap[authType.lower()]
  privLen = reqLenMap[privType.lower()]
  # From draft-blumenthal-aes-usm-04 section 3.1.2.1
  # Ceiling Dived of privLen by authLen
  concatCount = int(((privLen + (authLen-1))//authLen))
  count = 1
  while count < concatCount:
    localHash = hasher()
    #localHash.update(kulHash.decode("hex"))
    localHash.update(kulHash)
    #kulHash = kulHash + localHash.hexdigest()
    kulHash = kulHash + localHash.digest()
    count += 1
  # Truncate in case we have too much.
  kulHash = kulHash[: privLen]
  #return kul, kulHash
  return kul.hex(), kulHash.hex()

def main( args ):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument( "snmpUser", help="SNMP User Name" )
    parser.add_argument( "snmpGroup", help="SNMP Group Name" )
    parser.add_argument( "authPhrase", help="The authentication password/secret to be localized" )
    parser.add_argument( "authType", help="The authentication protocol (e.g., md5,sha,sha(224,256,384,512))" )
    parser.add_argument( "privPhrase", help="The privacy password/secret to be localized" )
    parser.add_argument( "privType", help="The privacy algorithm to use (e.g. des,aes,aes(192,256))" )
    parser.add_argument( "systemMAC", nargs="?", default=None, help="Switch SystemMAC address or leave blank to autogenerate")
    args = parser.parse_args()

    # Check authentication and privacy types
    assert args.authType in ( 'md5', 'sha', 'sha224', 'sha256', 'sha384', 'sha512' )
    if "none" in args.privType.lower():
        args.privType = None
    assert args.privType in ( None, 'des', 'aes', 'aes192', 'aes256' )

    # Generate SNMP Engine ID as we can't fetch it
    if args.systemMAC == None:
        print ("Generating Random engineID")
        engineId = genEngineID().hex()
    else:
        print ("Generating EOS engineID")
        engineId = eosEngineID(args.systemMAC)
    print ("Engine ID {}".format(engineId))

    # Generate config for SNMPv3 
    # Generate SNMP User
    authKu, authKul = localizePassphrase(args.authPhrase, args.authType, engineId, args.privType)
    privKu, privKul = localizePassphrase(args.privPhrase, args.authType, engineId, args.privType)
    snmpConf = "snmp-server user %s %s v3 localized %s auth %s %s priv %s %s\n" % (args.snmpUser, args.snmpGroup, engineId, args.authType, authKu, args.privType, privKul)
    print (snmpConf)

if __name__ == "__main__":
    import sys
    main( sys.argv[ 1: ] )
