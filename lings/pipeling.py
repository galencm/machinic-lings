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
import attr
import os
import functools
import glob
import importlib
import sys
#import local_tools
import logzero
import consul

try:
    logzero.logfile("/tmp/{}.log".format(os.path.basename(sys.argv[0])))
except Exception as ex:
    print(ex)

#change RouteMessage object to dict
@attr.s 
class RouteMessage():
    channel = attr.ib()
    contents = attr.ib()
    errors= attr.ib()

path = os.path.dirname(os.path.realpath(__file__))
pipeling_metamodel = metamodel_from_file(os.path.join(path,'pipeling.tx'))


def lookup(service):
    c = consul.Consul()
    services = {k:v for (k,v) in c.agent.services().items() if k.startswith("_nomad")}
    for k in services.keys():
        if services[k]['Service'] == service:
                service_ip,service_port = services[k]['Address'],services[k]['Port']
                return service_ip,service_port
                break
    return None,None
try:
    logzero.logfile("/tmp/{}.log".format(os.path.basename(sys.argv[0])))
except Exception as ex:
    print(ex)

redis_ip,redis_port = lookup('redis')

#mqtt_ip,mqtt_port = lookup('mqtt')

#redis_ip,redis_port = local_tools.lookup('redis')
r = redis.StrictRedis(host=redis_ip, port=str(redis_port),decode_responses=True)
pubsub = r.pubsub()


def add_pipe(dsl_string):
    """
        Args:
            dsl_string(str): A string that using pipeling grammar
    
        Returns:
            Tuple: name, key of created pipe
    """
    #TODO add overwrite? ie if name is same and hash changes, delete others with same name first?
    try:
        pipe = pipeling_metamodel.model_from_str(dsl_string)
    except Exception as ex:
        logger.error("Failed to parse {} using {}".format(dsl_string,pipeling_metamodel))
        logger.error(ex)
        return None,None
    remove_pipe(pipe.name)
    dsl_hash = hashlib.sha224(dsl_string.encode()).hexdigest()
    pipe_key = "pipe:{}:{}".format(pipe.name,dsl_hash)
    r.set(pipe_key,dsl_string)
    #some sort of success/failure return?
    return pipe.name,pipe_key


def remove_pipe(name=None,dsl_string=None):
    """Match and remove pipe(s) based on name, hashed contents or both

        Args:
            name(str): name of pipe
            dsl_string(str): string following pipeling grammar
    """
    if name is None and dsl_string is None:
        return

    if dsl_string is not None:
        dsl_hash = hashlib.sha224(dsl_string.encode()).hexdigest()
    else:
        dsl_hash = '*'

    if name is None or name is '':
        name="*"

    match_query = "pipe:{}:{}".format(name,dsl_hash)
    pipes = list(r.scan_iter(match=match_query))
    
    #do not pass empty list to redis
    if pipes:
        r.delete(*pipes)
        logger.info("removed pipe(s) {}".format(pipes))
    else:
        logger.info("no pipes to remove matching {}".format(match_query))


def pipe(name,glworb_key,glworb_field,*args):

    #['prepareleft', 'bar', 'glworb_binary_key_contents']
    # pipename     glworb_id glworb_key
    p = get_pipe(name)
    logger.info("pipe: {} {}".format(p,name))

    #def pipe_starti(glworb_uuid,glworb_key,prefix="glworb:",*args):

    logger.info("starting pipe for {} {}".format(glworb_key,glworb_field))
    piped_obj = None
    
    #multiprocessing? process_steps(target=)
    for step in p.pipe_steps:
        args = [arg.arg for arg in step.args]
        logger.info("{}{}".format(step,args))
        try:
            if '_' in args:
                args[args.index('_')] = glworb_key
                logger.debug('{} substituted for _'.format(glworb_key))
        except Exception as ex:
            print(ex)
            pass

        if step.call == 'pipe':
            pipe((args[0]),*args[1:])
        elif 'start' in step.call:
            #special first call, move to objects?
            #logger.info([s for s in globals() if s.startswith("pipe_")])
            piped_obj = globals()["pipe_"+step.call](glworb_key,glworb_field,*args)
            #    path = os.path.dirname(os.path.realpath(__file__))
        else:
            piped_obj = globals()["pipe_"+step.call](piped_obj,*args)

        #return 

def get_pipes(query_pattern="*",raw=False):
    match_query = "pipe:{}:*".format(query_pattern)
    pipes = list(r.scan_iter(match=match_query))
    # pipe:<name>:<contents hash>
    pipes = [s.split(":")[1] for s in pipes]
    if raw is True:
        return pipes
    else:
        logger.info(pipes)
        return [get_pipe(p) for p in pipes if get_pipe(p) is not None]

def get_pipe(name,raw=False):
    #names / hash could be different is pipe1:hash1 pipe1:hash2
    #for now only return first result
    match_query = "pipe:{}:*".format(name)
    try:
        pipes = list(r.scan_iter(match=match_query))[0]
    except IndexError as ex:
        logger.debug(ex)
        return None

    stored_pipe = r.get(pipes)
    logger.info(match_query)
    if stored_pipe:
        try:
            pipe = pipeling_metamodel.model_from_str(stored_pipe)
            if raw is True:
                return stored_pipe
            else:
                return pipe
        except Exception as ex:
            logger.warn(ex)
            return None

def compose(*functions):
    """Compose list of functions

        Args:
            *functions: list of functions

        Returns:
            func: composed functions
    """
    return functools.reduce(lambda f, g: lambda x: f(g(x)), functions, lambda x: x)
