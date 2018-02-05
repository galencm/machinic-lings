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
    Get rule
    """
    #use nargs='?', for first arg?
    #--pattern default no recognized
    # get by name
    # get by key name
    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("rule_name", default=None, nargs='?', help = "rule name")
    parser.add_argument('--name', default=None, help="get rule by name")
    parser.add_argument('--pattern', help="get rules by pattern ( '*' matches all )")
    parser.add_argument('-v', '--verbose', action="store_true", help="verbose")

    args = parser.parse_args()
    # use this to allow either
    # lings-rule-get --name foo
    # lings-rule-get foo
    # to work...
    #
    # match query is constructed in get_rule
    # but it would be useful to pass entire hash in too...

    # if no args, list all rules
    if args.rule_name is  None and args.name is None:
        args.pattern = '*'
        
    if args.rule_name is not None:
        args.name = args.rule_name

    if args.name is None and args.pattern is None:
        parser.print_help()

    if args.name is not None:
        print(ruling.get_rule(args.name,raw=True))

    if args.pattern is not None:
        print()
        for rule in ruling.get_rules(args.pattern,raw=True,verbose=args.verbose):
            if args.verbose:
                print(rule)
            print(ruling.get_rule(rule,raw=True))
            print()
