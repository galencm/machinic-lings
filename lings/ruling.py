# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2018, Galen Curwen-McAdams

import hashlib
import os
import consul
import redis
from logzero import logger
from textx.metamodel import metamodel_from_file

path = os.path.dirname(os.path.realpath(__file__))
ruling_metamodel = metamodel_from_file(os.path.join(path, 'ruling.tx'))

def lookup(service):
    c = consul.Consul()
    services = {k:v for (k, v) in c.agent.services().items() if k.startswith("_nomad")}
    for k in services.keys():
        if services[k]['Service'] == service:
                service_ip,service_port = services[k]['Address'], services[k]['Port']
                return service_ip, service_port
                break
    return None, None

redis_ip, redis_port = lookup('redis')

r = redis.StrictRedis(host=redis_ip, port=str(redis_port), decode_responses=True)
pubsub = r.pubsub()

def add_rule(dsl_string, expire=None):
    pass

def remove_rule(name=None, dsl_string=None):
    pass

def rule(name, glworb_key, env=None, *args):
    pass

def get_rules(query_pattern="*", raw=False, verbose=False):
    pass

def rule_xml2str(xml=None,raw=False):
    pass

def rule_str2xml(dsl_string=None,name=None,raw=False,file=None):
    pass
