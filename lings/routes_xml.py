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
    xml route
    """
    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--name', default=None, help="get route by hash name")
    parser.add_argument('--route', default=None, help="string of route enclosed in double quotes")

    args = parser.parse_args()
    if args.name is None and args.route is None:
        parser.print_help()

    if args.name is not None:
        print(routeling.route_str2xml(route_hash=args.name,raw=True))

    if args.route is not None:
        print(routeling.route_str2xml(dsl_string=args.route,raw=True))
