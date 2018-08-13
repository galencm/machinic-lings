# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2018, Galen Curwen-McAdams

from lxml import etree
import consul
import redis

def lookup(service):
    try:
        c = consul.Consul()
        services = {k:v for (k, v) in c.agent.services().items() if k.startswith("_nomad")}
        for k in services.keys():
            if services[k]['Service'] == service:
                    service_ip,service_port = services[k]['Address'], services[k]['Port']
                    return service_ip, service_port
                    break
        return None, None
    except Exception as ex:
        return None, None

redis_ip,redis_port = lookup('redis')
r = redis.StrictRedis(host=redis_ip, port=str(redis_port),decode_responses=True)

def state_str2xml(state_dict=None, state_address=None, raw=False, file=None):
    if state_address:
        state = r.hgetall(state_address)
        state_type, peripheral = state_address.split(":")

    root = etree.Element("state",type=state_type)

    for k,v in state.items():
        root.append( etree.Element("set",peripheral=peripheral, symbol=k, value=v) )

    if file is not None:
        # remove_blank_text to reformat on output
        # however seems to only indent 2 spaces
        # parser = etree.XMLParser(remove_blank_text=True)
        # TODO look into xlst style transforms
        parser = etree.XMLParser()
        file_tree = etree.parse(file, parser)
        file_root = file_tree.getroot()
        file_root.append(root)
        file_tree.write(file, pretty_print=True)

    if raw is True:
        return etree.tostring(root, pretty_print=True).decode()
    else:
        return root
