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
    Remove rule
    """
    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("rule_name", default=None, nargs='?', help = "rule name")
    parser.add_argument("--rule", required=False,help="string of rule enclosed in double quotes")
    parser.add_argument("--name", required=False,help="name of rule")
    parser.add_argument("-f","--file", required=False,help="file of rules 1 per line")

    args = parser.parse_args()

    if args.rule_name is not None:
        args.name = args.rule_name

    if args.file:
        if os.path.isfile(args.file):
            with open(args.file,'r') as f:
                for line in f.readlines():
                    try:
                        ruling.remove_rule(dsl_string=line)
                    except Exception as ex:
                        print(ex)
    elif args.rule:
        try:
            ruling.remove_rule(dsl_string=args.rule)
        except Exception as ex:
            print(ex)
    elif args.name:
        try:
            ruling.remove_rule(name=args.rule_name)
        except Exception as ex:
            print(ex)