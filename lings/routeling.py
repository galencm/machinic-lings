# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2017, Galen Curwen-McAdams

from textx.metamodel import metamodel_from_file
import uuid
import redis
import hashlib
from logzero import logger
import textwrap
import operator
from lings import routeling_basic_operations
import os
import zerorpc
import consul
import sys
from functools import wraps


import logzero
try:
    logzero.logfile("/tmp/{}.log".format(os.path.basename(sys.argv[0])))
except Exception as ex:
    print(ex)

def lookup(service):
    c = consul.Consul()
    services = {k:v for (k,v) in c.agent.services().items() if k.startswith("_nomad")}
    for k in services.keys():
        if services[k]['Service'] == service:
                service_ip,service_port = services[k]['Address'],services[k]['Port']
                return service_ip,service_port
                break
    return None,None

def fuzzy_lookup(service):
    c = consul.Consul()
    matched_services = []
    services = {k:v for (k,v) in c.agent.services().items() if k.startswith("_nomad")}
    for k in services.keys():
        if service in services[k]['Service']:
                sinfo = {
                'ip':services[k]['Address'],
                'port':services[k]['Port'],
                'service':services[k]['Service']
                }
                matched_services.append(sinfo)
    return matched_services


path = os.path.dirname(os.path.realpath(__file__))
routeling_metamodel = metamodel_from_file(os.path.join(path,'routeling.tx'))
redis_ip,redis_port = lookup('redis')
r = redis.StrictRedis(host=redis_ip, port=str(redis_port),decode_responses=True)
pubsub = r.pubsub()

def route_signal(channel="",payload=""):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # make function name formattable
            # using {function}
            kwargs['function'] = func.__name__
            #print(inspect.getargspec(func))
            signal_channel = channel.format(**locals()['kwargs'])
            signal_payload = payload.format(**locals()['kwargs'])
            r.publish(signal_channel,signal_payload)
            #r.publish(func.__name__,args)
            # cleanup 'function' from kwargs
            del kwargs['function']
            return func(*args, **kwargs)
        return wrapper
    return decorator

def find_route(source_channel=None,route_hash=None, contents=None):
    if source_channel is None or source_channel == '':
        source_channel = "*"
    if route_hash is None or route_hash == '':
        route_hash = "*"


    match_query="route:*:{}:{}".format(source_channel,route_hash)
    matches = list(r.scan_iter(match=match_query))
    logger.info(match_query,matches)
    routes = {}

    for rt in matches:
        #routes.append()
        routes[rt] = r.get(rt)
    return routes

def add_route(dsl_string):
    """
        Args:
            dsl_string(str): A string that using pipeling grammar
    
        Returns:
            Tuple: name, key of created pipe
    """
    #route:<route_name>:<origin_channel>:<hash of route>

    routes = dsl_string.split("\n")
    routes = [r+"\n" for r in routes if r]
    created = []
    logger.debug(routes)
    for rt in routes:
        try:
            route = routeling_metamodel.model_from_str(rt)
            logger.debug("parsed {} into {}".format(rt,route))
            for rl in route.route_rules:
                channel = rl.channel

                dsl_hash = hashlib.sha224(rt.encode()).hexdigest()
                logger.info("adding route with hash: {}".format(dsl_hash))
                try:
                    name = route.name
                except:
                    name="_"
                key = "route:{}:{}:{}".format(name,channel,dsl_hash)
                r.set(key,rt)
                watch_route_key(channel)
                created.append((name,key))
        except Exception as ex:
            logger.error("Failed to parse {} using {}".format(repr(rt),routeling_metamodel))
            logger.error(ex)
    return created

def watch_route_key(channel):
    #add to watched channels
    #"if '/foo' do pipe prepareleft '{payload}' glworb_binary_key_contents\n"
    r.sadd("watch:all",channel)

def remove_routes():
    match_query = "route:*:*:*"
    routes = list(r.scan_iter(match=match_query))
    if routes:
        r.delete(*routes)
        logger.info("removed routes(s) {}".format(routes))

def remove_route(dsl_string):
    """Match and remove pipe(s) based on name, hashed contents or both

        Args:
            name(str): name of pipe
            dsl_string(str): string following pipeling grammar
    """
    if not dsl_string.endswith('\n'):
        dsl_string+="\n"

    dsl_hash = hashlib.sha224(dsl_string.encode()).hexdigest()

    match_query = "route:*:*:{}".format(dsl_hash)
    routes = list(r.scan_iter(match=match_query))
    #remove from watch?
    if routes:
        r.delete(*routes)
        logger.debug("removed routes(s) {}".format(routes))
    else:
        logger.debug("no routes to remove matching {}".format(match_query))

def get_routes(query_pattern="*", raw=False):

    match_query = "route:{}".format(query_pattern)
    routes = list(r.scan_iter(match=match_query))
    if raw is True:
        routes = [s.split(":")[3] for s in routes]
        return routes
    else:
        logger.info(routes)
        routes = [s.split(":")[3] for s in routes]
        return [get_route(route_hash=r) for r in routes if get_route(route_hash=r) is not None]

    return routes

def get_route(dsl_string=None, route_hash=None, raw=False):
    #names / hash could be different is pipe1:hash1 pipe1:hash2
    #for now only return first result

    if dsl_string is not None:
        dsl_hash = hashlib.sha224(dsl_string.encode()).hexdigest()

    if route_hash is not None:
        dsl_hash = route_hash

    match_query = "route:*:*:{}".format(dsl_hash)
    logger.debug(match_query)
    try:
        routes = list(r.scan_iter(match=match_query))[0]
    except IndexError as ex:
        logger.debug("failed to get route {}".format(dsl_string))
        logger.debug(ex)
        return None

    stored_route = r.get(routes)
    if stored_route:
        try:
            route = routeling_metamodel.model_from_str(stored_route)
            if raw is True:
                return stored_route
            else:
                return route
        except Exception as ex:
            logger.warn(ex)
            return None
    else:
        return None

def comparator_symbol_to_string(comparator):
    if comparator == "<":
        result = "less than"
    elif comparator == ">":
        result =  "greater than"
    elif comparator == "<=":
        result =  "less than or equal to"
    elif comparator == ">=":
        result =  "greater than or equal to"
    elif comparator == "!=":
        result =  "does not equal"
    elif comparator == "==":
        result =  "equals"
    else:
        result = None
    return result

def route_xml2str(xml=None,raw=False):
    # placeholder
    # this needs to be generated when the ling
    # model is defined so it can use the same
    # processing as gsl
    pass

def route_str2xml(dsl_string=None,route_hash=None,raw=False):
    # This couples xml generation to the xml model used by gsl
    # If the model changes so will this code. There may also
    # be situations where reconstruction is not possible, since a
    # benefit of the model is its flexibility in specification and
    # synax.
    #
    # This is prototyping for lingen: use an xml model to define
    # a dsl (ling) which gsl outputs:
    #
    # * a python package structure
    #   * a textx .tx file
    #   * stub functions, including this one as defined in model
    #   * entry poing cli tools: *-add, *-run, *-remove, *-get, *-xml2str
    #   * generated tests
    # * a file that can be easily run as rpc service to be included with
    #   machines: for example, see 'pipe'
    #
    # register entrypoints using lings as toplevel ie: lings-fooling-add
    #
    # Then when xml model changes, regenerate ling code...

    # example route model:
    # <route trigger="/foo" call="create_glworb">
    #     <conditional type="less than or equal" value=".4" />
    #     <conditional type="greater than or equal" value="1" />
    #     <argument value="{'payload'}" />
    #     <argument value="{'from'}" />
    # </route>

    from lxml import etree

    if dsl_string:
        # unescape escaped newlines if from shell
        dsl_string = dsl_string.replace("\\n","\n")
        # peculiarity of route implementation, expects
        # to end with newline, will change hashes if not
        # used
        if not dsl_string.endswith("\n"):
            dsl_string+="\n"

    # pass both, None value will be ignored
    route = get_route(dsl_string=dsl_string,route_hash=route_hash)

    # a route was not found in db and dsl string
    # passed, try to parse dsl string...
    if not route and dsl_string:
        route = routeling_metamodel.model_from_str(dsl_string)

    for r in route.route_rules:
        print(r)
        root = etree.Element("route",trigger=r.channel,call=r.action)
        if r.left_compare:
            root.append( etree.Element("conditional",type=comparator_symbol_to_string(r.left_compare.comparator_symbol.symbol),
                                                    value=r.left_compare.comparator_value) )
        if r.right_compare:
            root.append( etree.Element("conditional",type=comparator_symbol_to_string(r.right_compare.comparator_symbol.symbol),
                                                    value=r.right_compare.comparator_value) )
        if r.args:
            for arg in r.args:
                root.append( etree.Element("argument",value=arg.arg) )

    if raw is True:
        return etree.tostring(root, pretty_print=True).decode()
    else:
        return root

def interpret_route(route,source_channel,payload):
    """Parse route rule(s) and route payload

        Args:
            route(str): a route rule to be parsed
            source_channel(str): source of payload
            payload(str):contents
    """
    logger.debug("{} {} {}".format(route,source_channel,payload))
    #grammer recognizes substitutions but use replace
    route = route.replace("{'from'}",source_channel)
    #added '' s around payload to allow correct parsing
    #of dashed-uuid-s
    try:
        #decode if from mqtt
        route = route.replace("{'payload'}","'{}'".format(payload.decode()))
    except:
        route = route.replace("{'payload'}","'{}'".format(payload))

    logger.debug("{} {} {} [after template substitutions]".format(route,source_channel,payload))

    routes = routeling_metamodel.model_from_str(route)
    #messy parsing...
    for route in routes.route_rules:
        try:
            try:
                result_left = comparate(route.left_compare.comparator_symbol.symbol,route.left_compare.comparator_value,payload.decode())
            except Exception as ex:
                result_left = True
            try:
                result_right = comparate(route.right_compare.comparator_symbol.symbol,payload.decode(),route.right_compare.comparator_value)
            except Exception as ex:
                result_right = True

            decision = result_left and result_right
            logger.info("{} and {} = {}".format(result_left,result_right,decision))
            if decision is True:
                args = []
                for arg in route.args:
                    print(arg)
                    try:
                        print(arg.arg)
                        args.append(arg.arg)
                        try:
                            print(arg.arg.sub)
                        except Exception as ex:
                            print(ex)

                    except Exception as ex:
                        print(ex)

                #builtins = ['mapii','mapix','mapxi','mapxx']
                #if route.action in builtins:
                if hasattr(routeling_basic_operations,route.action.lower()):
                    #use dict instead of custom obj
                    rm = {'channel':source_channel,
                          'contents':payload,
                          'errors':''
                    }
                    rargs = [rm] + args
                    logger.debug("builtin rpc --> {} + {}".format(route.action,rargs))
                    try:
                        getattr(routeling_basic_operations, route.action.lower())(*rargs)
                    except Exception as ex:
                        logger.warn(ex)
                elif route.action == 'pipe':
                    logger.info("PIPE {} {}".format(route.action,args))
                    #with pipe assume message is a glworb id?
                    #rargs = [] + rargs
                    #put into a todo queue?
                    #query route.action.lower() for rpc address
                    #another option:
                    #https://www.hashicorp.com/blog/replacing-queues-with-nomad-dispatch/
                    #TODO queue here...

                    for service in fuzzy_lookup('zerorpc-'):
                        logger.info("trying service {}".format(service['service']))
                        zc = zerorpc.Client()
                        zc.connect("tcp://{}:{}".format(service['ip'],service['port']))
                        result = zc(route.action.lower(),*args)
                        logger.info(result)
                else:
                    for service in fuzzy_lookup('zerorpc-'):
                        try:
                            logger.info("trying service {}".format(service['service']))
                            zc = zerorpc.Client()
                            zc.connect("tcp://{}:{}".format(service['ip'],service['port']))
                            result = zc(route.action.lower(),*args)
                            logger.info(result)
                        except Exception as ex:
                            print(ex)

                    #rpc_ip,rpc_port = local_tools.lookup('zerorpc-image')
                    # zc = zerorpc.Client()
                    # zc.connect("tcp://{}:{}".format(rpc_ip,rpc_port))
                    # result = zc(route.action.lower(),*args)
                    # logger.info(result)
                    #rpc(*rargs)
        except Exception as ex:
            logger.warn(ex)

def comparate(comparator,a,b,try_to_cast=True):
    """Given a string comparator and two inputs return results.

        Args:
            comparator(str): 
            a:
            b:

        Returns:
            bool: comparator results
    """
    if try_to_cast:
        try:
            a = float(a)
            b = float(b)
        except Exception as ex:
            logger.debug(ex)
            pass

    result = False

    if comparator == "<":
        result =  operator.lt(a,b)
    elif comparator == ">":
        result =  operator.gt(a,b)
    elif comparator == "<=":
        result =  operator.le(a,b)
    elif comparator == ">=":
        result =  operator.ge(a,b)
    elif comparator == "!=":
        result =  operator.ne(a,b)
    elif comparator == "==":
        result =  operator.eq(a,b)
    else:
        result = False

    logger.debug("{a} {symbol} {b} = {result}".format(a=a,b=b,symbol=comparator,result=result))
    return result