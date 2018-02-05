#!/usr/bin/python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
from lings import ruling

def insert_into(string, substring, index):

    return string[:index] + substring + string[index:]

def print_to_terminal(lines, pretty=True):

    color = "\033[0;36m"
    color_end = "\033[0;0m"

    for line_num,line in enumerate(lines):
        if pretty:
            if line_num == 0 or line_num == len(lines)-1:
                print("{}{:<4}{}{}".format(color,line_num,color_end,line))
            else:
                print("{:<4}{}".format(line_num,line))
        else:
            print(line)

def main():
    """
    Modify rule
    """
    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("name", default=None, help = "rule name")
    parser.add_argument("rule_string", nargs='?', default=None, help = "string to be used with rule")
    parser.add_argument('--append', action='store_true', help="append into rule")
    parser.add_argument('--insert', type=int, help="insert into rule at line")
    parser.add_argument('--overwrite', type=int, help="insert and overwrite into rule at line")
    parser.add_argument('--remove', type=int, help="remove line from rule")
    parser.add_argument('--copy', help="copy rule to newname")
    parser.add_argument('--no-pretty', action='store_false', help="do not format output with line numbers or color")
    parser.add_argument('--preview', action='store_true', help="show rule without modifying")
    parser.add_argument("-x","--expire", type=int, default=0, required=False,help="temporary rule, expires after specified seconds")

    args = parser.parse_args()
    
    rule_to_modify = ruling.get_rule(args.name,raw=True)
    rule_unmodified = rule_to_modify

    if args.copy:
        rule_to_modify = rule_to_modify.replace(args.name,args.copy,1)
        ruling.add_rule(rule_to_modify, expire=args.expire)
        print(rule_to_modify)
        return

    # do not remove existing newlines
    rule_to_modify =' '.join(rule_to_modify.split(" "))

    rule_start = rule_to_modify.find('{')
    if not rule_to_modify[rule_start+1] == "\n":
        rule_to_modify = insert_into(rule_to_modify,"\n",rule_start+1)

    rule_end = rule_to_modify.rfind('}')
    if not rule_to_modify[rule_end-1] == "\n":
        rule_to_modify = insert_into(rule_to_modify,"\n",rule_end)

    rule_to_modify = rule_to_modify.split("\n")

    if args.append:
        rule_to_modify.insert(-1, args.rule_string)
    elif args.insert:
        if (args.insert >= 1) and (args.insert < len(rule_to_modify)-1 ):
            rule_to_modify.insert(args.insert, args.rule_string)
    elif args.overwrite:
        if (args.overwrite >= 1) and (args.overwrite < len(rule_to_modify)-1 ):
            rule_to_modify[args.overwrite] = args.rule_string
    elif args.remove:
        if (args.remove >= 1) and (args.remove < len(rule_to_modify)-1 ):
            del rule_to_modify[args.remove]
    elif args.preview:
        print_to_terminal(rule_to_modify,args.no_pretty)
        return

    print_to_terminal(rule_to_modify,args.no_pretty)

    ruling.add_rule("\n".join(rule_to_modify), expire=args.expire)
