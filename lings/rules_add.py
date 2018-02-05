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
    Add rule
    """
    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("rule_name", default=None, nargs='?', help="",)
    parser.add_argument("--rule", required=False,help="string of rule enclosed in double quotes")
    parser.add_argument("-f","--file", required=False,help="file of rules 1 per line")
    parser.add_argument("-x","--expire", type=int, default=0, required=False,help="temporary rule, expires after specified seconds")

    args = parser.parse_args()

    if args.file:
        if os.path.isfile(args.file):
            with open(args.file,'r') as f:
                for line in f.readlines():
                    try:
                        ruling.add_rule(line)
                    except Exception as ex:
                        print(ex)
    elif args.rule:
        try:
            ruling.add_rule(args.rule,expire=args.expire)
        except Exception as ex:
            print(ex)
    elif args.rule_name is not None:
        try:
            ruling.add_rule("rule {} {{}}".format(args.rule_name),expire=args.expire)
        except Exception as ex:
            print(ex)
