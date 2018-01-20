#!/usr/bin/python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
from lings import pipeling
import sys
import os

def main():
    """
    Run pipe
    """
    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('name',  help="name of pipe")
    parser.add_argument('uuid', help="uuid or hash to use as context for pipe")
    parser.add_argument('args', nargs='*', default=[], help='arguments for pipe')
    parser.add_argument('--prefix', default="glworb:", help='key prefix')

    args = parser.parse_args()

    # prepend prefix to uuid if needed
    if not args.uuid.startswith(args.prefix):
        args.uuid = args.prefix + args.uuid

    pipeling.pipe(args.name, args.uuid, *args.args)