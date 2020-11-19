# Copyright (c) 2020, Arista Networks, Inc.
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

"""
Basic argparser to be reused in examples.

Mirrors the usage of the -auth flag in the arista go monorepo for
convenience and convention's sake
"""
import argparse
import os.path

AUTH_HELP = """
Authentication scheme used to connect to CloudVision. Possible values

    "none": no authentication
    "none-tls[,{caFile}]": no authentication, TLS encryption
    "token,{tokenFile}[,{caFile}]": access token based authentication
    "certs,{certFile},{keyFile}[,{caFile}]": client-side certificate
"""


class AuthAction(argparse.Action):
    """
    AuthAction is responsible for parsing arguments to the grpc_client.

    Possible values currently are

    'none': no authentication
    'none-tls[,{caFile}]': no authentication, TLS encryption
    'token,{tokenFile}[,{caFile}]': access token based authentication
    'certs,{certFile},{keyFile}[,{caFile}]': client-side certificate
    """
    NONE = 'none'
    NONE_TLS = 'none-tls'
    CERTS = 'certs'
    TOKEN = 'token'

    VALID_AUTHS = [NONE, NONE_TLS, CERTS, TOKEN]

    def __init__(self, option_strings, dest, nargs=None, const=None,
                 default=None, type=None, choices=None, required=False,
                 help=None, metavar=None):
        argparse.Action.__init__(self, option_strings, dest=dest, nargs=nargs,
                                 default=default, type=type, choices=choices,
                                 required=required, help=help, metavar=metavar)

    def __call__(self, parser, namespace, values, option_string=None):
        if not isinstance(values, str):
            err = "%s is not a valid auth type"
            raise argparse.ArgumentTypeError(self, err % values)

        split = values.split(',')
        authtype = split[0]
        authargs = split[1:]

        if authtype not in self.VALID_AUTHS:
            err = "%s is not a valid authentication scheme"
            raise argparse.ArgumentError(self, err % authtype)

        opts = {
            'caFile': None,
            'certFile': None,
            'keyFile': None,
            'tokenFile': None,
        }

        if authtype == self.NONE:
            pass
        elif authtype == self.NONE_TLS:
            if len(authargs) != 1:
                err = "expected 1 argument for 'none-tls' auth, got %d"
                raise argparse.ArgumentError(self, err % len(authargs))

            opts['caFile'] = os.path.expanduser(authargs[0])
        elif authtype == self.CERTS:
            if len(authargs) < 2 or len(authargs) > 3:
                err = "expected 2-3 arguments for 'certs' auth got %d"
                raise argparse.ArgumentError(self, err % len(authargs))

            opts['certFile'] = os.path.expanduser(authargs[0])
            opts['keyFile'] = os.path.expanduser(authargs[1])
            if len(authargs) == 3:
                opts['caFile'] = os.path.expanduser(authargs[2])
        elif authtype == self.TOKEN:
            if len(authargs) != 1 and len(authargs) != 2:
                err = "expected exactly 1 argument for 'token' auth, got %d"
                raise argparse.ArgumentError(self, err % len(authargs))
            opts['tokenFile'] = os.path.expanduser(authargs[0])
            if len(authargs) == 2:
                opts['caFile'] = os.path.expanduser(authargs[1])

        for opt, val in opts.items():
            setattr(namespace, opt, val)
        setattr(namespace, self.dest, values)  # also set the base auth string


base = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
base.add_argument('--apiserver', help='URL and port of CVP apiserver to connect to'
                  'in the format HOST:PORT i.e. (apiserver.examplecvp.com:11002)')
base.add_argument('--auth', action=AuthAction, default='', help=AUTH_HELP)


if __name__ == '__main__':
    base.parse_args()
