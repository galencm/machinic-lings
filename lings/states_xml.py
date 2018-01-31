#!/usr/bin/python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

def main():
    """
    xml state
    """
    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("state_name", default=None, nargs='?', help = "pipe name")
    parser.add_argument('--name', default=None, help="get state by name")
    parser.add_argument('--file', default=None, help="xml file to write output into")

    args = parser.parse_args()

    if args.state_name is not None:
        args.name = args.state_name

    if args.state_name is not None:
        print(stateling.state_str2xml(name=args.name, raw=True, file=args.file))

    if args.state_name is None and args.name is None:
        parser.print_help()