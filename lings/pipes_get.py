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
    #use nargs='?', for first arg?
    #--pattern default no recognized
    # get by name
    # get by key name
    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pipe_name", default=None, nargs='?', help = "pipe name")
    parser.add_argument('--name', default=None, help="get pipe by name")
    parser.add_argument('--pattern', help="get pipes by pattern ( '*' matches all )")
    parser.add_argument('-v', '--verbose', action="store_true", help="verbose")

    args = parser.parse_args()
    # use this to allow either
    # lings-pipe-get --name foo
    # lings-pipe-get foo
    # to work...
    #
    # match query is constructed in get_pipe
    # but it would be useful to pass entire hash in too...

    # if no args, list all pipes
    if args.pipe_name is  None and args.name is None:
        args.pattern = '*'
        
    if args.pipe_name is not None:
        args.name = args.pipe_name

    if args.name is None and args.pattern is None:
        parser.print_help()

    if args.name is not None:
        print(pipeling.get_pipe(args.name,raw=True))

    if args.pattern is not None:
        print()
        for pipe in pipeling.get_pipes(args.pattern,raw=True,verbose=args.verbose):
            if args.verbose:
                print(pipe)
            print(pipeling.get_pipe(pipe,raw=True))
            print()
