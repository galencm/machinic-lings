#!/usr/bin/python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
from lings import routeling
from lings import routeling_basic_operations as route_ops
import sys
import os

def main():
    """
    Run pipe
    """
    # two possibilities for what running a route does:
    # 1)  get existing route startpoint from hash and 
    #       send args there
    #       $ lings-route-run route_hash args
    #
    # 2)  use fresh routestring, add route,send args, remove route

    #def interpret_route(route,source_channel,payload):


    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('route_name',  help="hash of route")
    parser.add_argument('--message', default="", help="message to send")
    parser.add_argument('--uuid', help="uuid or hash to send as context for route")
    parser.add_argument('--prefix', default="glworb:", help='uuid prefix')
    parser.add_argument('--name', default=None, help='route hash')
    parser.add_argument('--protocol',default='redis', choices=('redis','mqtt'), help='protocol to use for publishing')

    args = parser.parse_args()

    if args.route_name is not None:
        args.name = args.route_name

    # prepend prefix to uuid if needed
    if args.uuid and not args.uuid.startswith(args.prefix):
        args.uuid = args.prefix + args.uuid

    # get startpoint
    route = routeling.get_route(route_hash=args.name)
    for r in route.route_rules:
        print("sending message: {} on channel: {}".format(args.message, r.channel))
        if args.protocol == 'redis':
            route_ops.internal_to_internal(r.channel, args.message)
        elif args.protocol == 'mqtt':
            route_ops.external_to_external(r.channel, args.message)

