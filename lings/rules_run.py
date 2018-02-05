#!/usr/bin/python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
from lings import ruling
import sys
import os
import json

def main():
    """
    Run rule
    """
    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('name',  help="name of rule")
    parser.add_argument('uuid', nargs="?", default=None, help="uuid or hash to use as context for rule")
    parser.add_argument('--prefix', default="glworb:", help='key prefix')
    parser.add_argument('--dict', type=json.loads, default={}, help='dict, uses json.loads to parse')

    args = parser.parse_args()

    # prepend prefix to uuid if needed
    if not args.uuid.startswith(args.prefix):
        args.uuid = args.prefix + args.uuid

    ruling.rule(args.name, glworb_key=args.uuid, glworb_dict=args.dict)
