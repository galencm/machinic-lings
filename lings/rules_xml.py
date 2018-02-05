#!/usr/bin/python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
from lings import ruling
import sys
import os

def main():
    """
    xml rule
    """
    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("rule_name", default=None, nargs='?', help = "rule name")
    parser.add_argument('--name', default=None, help="get rule by name")
    parser.add_argument('--rule', default=None, help="string of rule enclosed in double quotes")
    parser.add_argument('--file', default=None, help="xml file to write output into")

    args = parser.parse_args()

    if args.rule_name is not None:
        args.name = args.rule_name

    if args.name is None and args.rule is None:
        parser.print_help()

    if args.name is not None:
        print(ruling.rule_str2xml(name=args.name,raw=True, file=args.file))

    if args.rule is not None:
        print(ruling.rule_str2xml(dsl_string=args.rule,raw=True, file=args.file))
