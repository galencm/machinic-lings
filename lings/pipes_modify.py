#!/usr/bin/python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
from lings import pipeling

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
    Modify pipe
    """
    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("name", default=None, help = "pipe name")
    parser.add_argument("pipe_string", nargs='?', default=None, help = "string to be used with pipe")
    parser.add_argument('--append', action='store_true', help="append into pipe")
    parser.add_argument('--insert', type=int, help="insert into pipe at line")
    parser.add_argument('--overwrite', type=int, help="insert and overwrite into pipe at line")
    parser.add_argument('--remove', type=int, help="remove line from pipe")
    parser.add_argument('--copy', help="copy pipe to newname")
    parser.add_argument('--no-pretty', action='store_false', help="do not format output with line numbers or color")
    parser.add_argument('--preview', action='store_true', help="show pipe without modifying")

    args = parser.parse_args()
    
    pipe_to_modify = pipeling.get_pipe(args.name,raw=True)
    pipe_unmodified = pipe_to_modify

    if args.copy:
        pipe_to_modify = pipe_to_modify.replace(args.name,args.copy,1)
        pipeling.add_pipe(pipe_to_modify)
        print(pipe_to_modify)
        return

    # do not remove existing newlines
    pipe_to_modify =' '.join(pipe_to_modify.split(" "))

    pipe_start = pipe_to_modify.find('{')
    if not pipe_to_modify[pipe_start+1] == "\n":
        pipe_to_modify = insert_into(pipe_to_modify,"\n",pipe_start+1)

    pipe_end = pipe_to_modify.rfind('}')
    if not pipe_to_modify[pipe_end-1] == "\n":
        pipe_to_modify = insert_into(pipe_to_modify,"\n",pipe_end)

    pipe_to_modify = pipe_to_modify.split("\n")

    if args.append:
        pipe_to_modify.insert(-1, args.pipe_string)
    elif args.insert:
        if (args.insert >= 1) and (args.insert < len(pipe_to_modify)-1 ):
            pipe_to_modify.insert(args.insert, args.pipe_string)
    elif args.overwrite:
        if (args.overwrite >= 1) and (args.overwrite < len(pipe_to_modify)-1 ):
            pipe_to_modify[args.overwrite] = args.pipe_string
    elif args.remove:
        if (args.remove >= 1) and (args.remove < len(pipe_to_modify)-1 ):
            del pipe_to_modify[args.remove]
    elif args.preview:
        print_to_terminal(pipe_to_modify,args.no_pretty)
        return

    print_to_terminal(pipe_to_modify,args.no_pretty)

    pipeling.add_pipe("\n".join(pipe_to_modify))
