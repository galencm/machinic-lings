#!/usr/bin/python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2018, Galen Curwen-McAdams

import argparse
from lings import routeling
import sys
import os
import time
import queue
import threading

def main():
    """
    Gather messages from routes
    """

    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--max-wait', type=int, help="exit after max time, regardless of number collected")
    parser.add_argument('--pattern', default="*", help="message pattern to match using unix-style pattern matching")
    # parser.add_argument('--protocol',default='redis', choices=('redis','mqtt'), help='protocol to use for publishing')
    parser.add_argument('--collect', type=int, help='number to of matches to collect. When reached, write results to stdout and exit')
    parser.add_argument('--channels', default=["*"], nargs='+', help='channels to listen on. Unix-style pattern matching works')

    args = parser.parse_args()

    q = queue.Queue()
    gatherer_stop_signal = threading.Event()
    monitor_stop_signal = threading.Event()

    monitor_thread = threading.Thread(target=timed_gather, args=(args.pattern, args.channels, q, args.max_wait, gatherer_stop_signal, monitor_stop_signal))
    monitor_thread.start()

    results = []
    while monitor_thread.isAlive() and (True if not args.collect else len(results) < args.collect):
        while not q.empty() and (True if not args.collect else len(results) < args.collect):
            results.append(q.get())

    monitor_stop_signal.set()
    gatherer_stop_signal.set()
    # monitor_thread.join()
    for result in results:
        sys.stdout.write(result+'\n')
        sys.stdout.flush()

def timed_gather(pattern, channels, q, max_wait, stop_signal, this_stop):
    gatherer = threading.Thread(target=routeling.listen, args=(pattern, channels, q, stop_signal))
    gatherer.start()
    wait = 0
    while(not this_stop.is_set()) and (True if not max_wait else wait < max_wait):
        time.sleep(1)
        wait += 1
    stop_signal.set()
