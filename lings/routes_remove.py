#!/usr/bin/python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
from lings import routeling
import sys
import os

def main():
    """
    Add route
    """
    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    #parser.add_argument("route", help="",required=False )
    parser.add_argument("route_string", default=None, nargs='?', help = "string of route enclosed in double quotes")
    parser.add_argument("--route", required=False,help="string of route enclosed in double quotes")
    parser.add_argument("-f","--file", required=False,help="file of routes 1 per line")

    args = parser.parse_args()

    if args.route_string is not None:
        args.route = args.route_string

    if args.file:
        if os.path.isfile(args.file):
            with open(args.file,'r') as f:
                for line in f.readlines():
                    try:
                        routeling.remove_route(line)
                    except Exception as ex:
                        print(ex)
    elif args.route:
        try:
            routeling.remove_route(args.route)
        except Exception as ex:
            print(ex)