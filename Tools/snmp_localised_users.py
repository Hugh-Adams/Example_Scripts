#!/usr/bin/env python
# Copyright (c) 2008-2019 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

# "v3localize": accepts the passphrase, the auth type, and
# optionally the engineID and the privacy type, to create a localized hex string
# that can be configured directly on the switch.
#
import uuid
import hashlib
import re

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

def _hasher( authType ):
    if authType == 'md5':
        hasher = hashlib.md5           # pylint: disable-msg=E1101
    elif authType == 'sha':
        hasher = hashlib.sha1          # pylint: disable-msg=E1101
    elif authType == 'sha224':
        hasher = hashlib.sha224        # pylint: disable-msg=E1101
    elif authType == 'sha256':
        hasher = hashlib.sha256        # pylint: disable-msg=E1101
    elif authType == 'sha384':
        hasher = hashlib.sha384        # pylint: disable-msg=E1101
    elif authType == 'sha512':
        hasher = hashlib.sha512        # pylint: disable-msg=E1101
    else:
        hasher = None
    return hasher

def keyFromPassphrase( phrase, authType ):
    """Generates a key from a passphrase as describe in RFC 2574 section A.2.
    authType should be 'md5', 'sha', or 'sha(224|256|384|512)'."""
    hasher = _hasher( authType )
    hashVal = hasher()            # pylint: disable-msg=W0622
    bytesLeft = 1048576
    concat = phrase.encode('utf-8')
    while len( concat ) < 64:
        concat += phrase.encode('utf-8')
    concatLen = len( concat )
    while bytesLeft > concatLen:
        hashVal.update( concat )
        bytesLeft -= concatLen
    if bytesLeft > 0:
        hashVal.update( concat[ 0 : bytesLeft ] )
    ku = hashVal.digest() 
    return ku

def localizePassphrase( phrase, authType, engineId, privType=None ):
    """Performs a key localization as described in RFC 2574 section 2.6.
    phrase is the plain ASCII passphrase.
    authType should be 'md5', 'sha', or 'sha(224|256|384|512)'.
    engineId is the *binary* value of the engineID.  (Not
    "8000757105..." but "\x80\x00\x75\x71\x05...")
    privType specifies the privacy protocol, like 'des', 'aes',
    'aes192' or 'aes256'.  This is needed when we need to create
    a longer Localized Key (kul) for a stronger privacy protocol."""

    ku = keyFromPassphrase( phrase, authType )
    hasher = _hasher( authType )
    localHash = hasher()
    localHash.update(ku + engineId + ku)
    authHash = localHash.digest()
    kul = localHash.digest()
    if privType is not None:
        bitsRequired = {
                'des': 128,
                'aes': 128,
                'aes192': 192,
                'aes256': 256,
                }[ privType.lower() ]
        # From draft-blumenthal-aes-usm-04 section 3.1.2.1
        while (len( kul * 8)) < bitsRequired:
            localHash = hasher()
            localHash.update(kul) 
            kul = kul + localHash.digest()
        # Truncate in case we have too much.
        kul = kul[0:int(bitsRequired/8)] # Kul is represented in bytes
    else:
        kul = None
    return authHash,kul

def main( args ):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument( "passphrase", help="The authentication or privacy passphrase to be localized" )
    parser.add_argument( "authType", help="The authentication protocol (e.g., aes, aes256)" )
    parser.add_argument( "privType", nargs="?", default=None, help="The privacy algorithm in use.  Required when localizing a privacy passphrase when using aes192 or aes256." )
    parser.add_argument("engineId", nargs="?", default=None, help="The engineID to which to localize the passphrase, leave blank to auto generate")
    args = parser.parse_args()
    assert args.authType in ( 'md5', 'sha', 'sha224', 'sha256', 'sha384', 'sha512' )
    if "none" in args.privType.lower():
        args.privType = None
    assert args.privType in ( None, 'des', 'aes', 'aes192', 'aes256' )
    if args.engineId == None:
        print ("Generating engineID")
        engineId = genEngineID()
    else:
        print ("Received engineID")
        engineId = bytearray.fromhex(args.engineId)
        print ("Engine ID {}".format(engineId.hex()))
    hashValues = localizePassphrase(args.passphrase, args.authType, engineId, args.privType)
    if hashValues[1]:
        privHash = hashValues[1].hex()
    else:
        privHash = ""
    print ("Auth Hash {} \nPriv Hash {}".format(hashValues[0].hex(),privHash))

if __name__ == "__main__":
    import sys
    main( sys.argv[ 1: ] )
