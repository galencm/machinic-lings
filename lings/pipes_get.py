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
    Get pipe
    """
    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--name', default=None, help="get pipe by name")
    parser.add_argument('--pattern', help="get pipes by pattern ( '*' matches all )")

    args = parser.parse_args()
    if args.name is None and args.pattern is None:
        parser.print_help()

    if args.name is not None:
        print(pipeling.get_pipe(args.name,raw=True))

    if args.pattern is not None:
        for pipe in pipeling.get_pipes(args.pattern,raw=True):
            print(pipeling.get_pipe(pipe,raw=True))
