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
    Add pipe
    """
    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pipe_name", default=None, nargs='?', help = "pipe name")
    parser.add_argument("--pipe", required=False,help="string of pipe enclosed in double quotes")
    parser.add_argument("--name", required=False,help="name of pipe")
    parser.add_argument("-f","--file", required=False,help="file of pipes 1 per line")

    args = parser.parse_args()

    if args.pipe_name is not None:
        args.name = args.pipe_name

    if args.file:
        if os.path.isfile(args.file):
            with open(args.file,'r') as f:
                for line in f.readlines():
                    try:
                        pipeling.remove_pipe(dsl_string=line)
                    except Exception as ex:
                        print(ex)
    elif args.pipe:
        try:
            pipeling.remove_pipe(dsl_string=args.pipe)
        except Exception as ex:
            print(ex)
    elif args.name:
        try:
            pipeling.remove_pipe(name=args.pipe_name)
        except Exception as ex:
            print(ex)