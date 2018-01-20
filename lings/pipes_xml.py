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
    xml pipe
    """
    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pipe_name", default=None, nargs='?', help = "pipe name")
    parser.add_argument('--name', default=None, help="get pipe by name")
    parser.add_argument('--pipe', default=None, help="string of pipe enclosed in double quotes")

    args = parser.parse_args()

    if args.pipe_name is not None:
        args.name = args.pipe_name

    if args.name is None and args.pipe is None:
        parser.print_help()

    if args.name is not None:
        print(pipeling.pipe_str2xml(name=args.name,raw=True))

    if args.pipe is not None:
        print(pipeling.pipe_str2xml(dsl_string=args.pipe,raw=True))
