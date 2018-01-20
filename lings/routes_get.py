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
    Get route
    """
    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("route_name", default=None, nargs='?', help = "route name")
    parser.add_argument('--name', default=None, help="get route by hash name")
    parser.add_argument('--pattern', default='*', help="get routes by pattern ( '*' matches all )")

    args = parser.parse_args()
    
    if args.route_name is not None:
        args.name = args.route_name

    if args.name is None and args.pattern is None:
        parser.print_help()

    if args.name is not None:
        print(routeling.get_route(route_hash=args.name, raw=True))

    if args.pattern is not None:
        for route in routeling.get_routes(args.pattern, raw=True):
            print(routeling.get_route(route_hash=route, raw=True))
