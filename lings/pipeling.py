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

redis_ip,redis_port = lookup('redis')

r = redis.StrictRedis(host=redis_ip, port=str(redis_port),decode_responses=True)
pubsub = r.pubsub()


def add_pipe(dsl_string, expire=None):
    """
        Args:
            dsl_string(str): A string that using pipeling grammar
    
        Returns:
            Tuple: name, key of created pipe
    """
    #TODO add overwrite? ie if name is same and hash changes, delete others with same name first?

    # unescape escaped newlines
    if expire is None:
        expire = 0

    dsl_string = dsl_string.replace("\\n","\n")
    logger.info("add pipe from string: {}".format(repr(dsl_string)))
    try:
        pipe = pipeling_metamodel.model_from_str(dsl_string)
    except Exception as ex:
        logger.error("Failed to parse {} using {}".format(dsl_string,pipeling_metamodel))
        logger.error(ex)
        return None,None
    logger.info("clearing existing: {}".format(pipe.name))
    remove_pipe(pipe.name)
    for step in pipe.pipe_steps:
        args = [arg.arg for arg in step.args]
        logger.debug("{} {}".format(step.call,args))

    dsl_hash = hashlib.sha224(dsl_string.encode()).hexdigest()
    pipe_key = "pipe:{}:{}".format(pipe.name,dsl_hash)
    r.set(pipe_key,dsl_string)
    logger.info("added pipe: {}".format(pipe_key))
    if expire > 0:
        r.expire(pipe_key,expire)
        logger.info("expires in: {}".format(expire))
        logger.info("ttl: {}".format(r.ttl(pipe_key)))

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


def pipe(name,glworb_key,env=None,*args):

    if env is None:
        env = {}

    # if it looks like a key:value
    # pair, add it to env dict
    # use zzzz as delimiter until grammar modified
    # nonsense values will not interfere
    for arg in args:
        if "zzzz" in arg:
            k, v = arg.split("zzzz")
            env[k] = v

    logger.debug("{} {} {}".format(name,glworb_key,args))
    p = get_pipe(name)
    logger.info("pipe: {} {}".format(name, p))
    logger.info("starting pipe: {} for {}".format(name, glworb_key))

    context = {'uuid':glworb_key,
                'key':'image_binary_key',
                'binary_prefix':'glworb_binary:'}

    logger.info("env: {}".format(env))
    logger.info("context: {}".format(context))

    context.update(env)

    for step in p.pipe_steps:
        step_args = [arg.arg for arg in step.args]
        logger.debug("step: {} args: {}".format(step.call,step_args))

        if step.call == 'pipe':
            logger.info("calling func: {} with context: {} args: {}".format(step_args[0], context, step_args[1:]))
            pipe(step_args[0], glworb_key, *step_args[1:])
        else:
            logger.info("calling func: {} with context: {} args: {}".format(step.call, context, step_args))
            result = rpc_any(step.call, context, step_args)
            if result:
                context = result

    # publish that pipe has completed 
    delimiter = "/"
    if delimiter == '/':
        pipe_channel = "{delimiter}pipe{delimiter}{name}{delimiter}completed".format(delimiter=delimiter, name=name)
    else:
        pipe_channel = "pipe{delimiter}{name}{delimiter}completed".format(delimiter=delimiter, name=name)

    r.publish(pipe_channel, glworb_key)
        # try:
        #     if '_' in args:
        #         args[args.index('_')] = glworb_key
        #         logger.debug('{} substituted for _'.format(glworb_key))
        # except Exception as ex:
        #     print(ex)
        #     pass
        # if step.call == 'pipe':
        #     pipe((args[0]),*args[1:])
        # else:
        #     context =

def rpc_any(func, context, call_args):
    import zerorpc
    for service in fuzzy_lookup("zerorpc-"):
        try:
            result = None
            logger.info("trying service {}".format(service))
            print("tcp://{}:{}".format(service['ip'],service['port']))
            logger.info("call -> func: {} context: {} args: {}".format(func, context, call_args))
            zc = zerorpc.Client()
            zc.connect("tcp://{}:{}".format(service['ip'],service['port']))
            result = zc(func, context, *call_args)
            if result is not None:
                logger.info("Success!")
            logger.info("call result: {}".format(result))
        except Exception as ex:
            logger.warn("{}".format(service))
            logger.warn(ex)

def get_pipes(query_pattern="*",raw=False, verbose=False):
    match_query = "pipe:{}:*".format(query_pattern)
    pipes = list(r.scan_iter(match=match_query))
    # pipe:<name>:<contents hash>
    if verbose is False:
        pipes = [s.split(":")[1] for s in pipes]

    if raw is True:
        return pipes
    else:
        logger.info(pipes)
        return [get_pipe(p) for p in pipes if get_pipe(p) is not None]

def get_pipe(name,raw=False):
    #names / hash could be different is pipe1:hash1 pipe1:hash2
    #for now only return first result
    if not name.startswith("pipe:"):
        match_query = "pipe:{}:*".format(name)
    else:
        match_query = "{}".format(name)

    try:
        pipes = list(r.scan_iter(match=match_query))[0]
    except IndexError as ex:
        logger.debug(ex)
        return None

    stored_pipe = r.get(pipes)
    #logger.info(match_query)
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

def pipe_xml2str(xml=None,raw=False):
    # placeholder
    # this needs to be generated when the pipe
    # model is defined so it can use the same
    # processing as gsl
    pass

def pipe_str2xml(dsl_string=None,name=None,raw=False,file=None):

    if dsl_string is not None:
        try:
            pipe = pipeling_metamodel.model_from_str(dsl_string)
        except Exception as ex:
            logger.error(ex)

    if name is not None:
        pipe = get_pipe(name=name)

    # see notes in routeling on lingen
    from lxml import etree

    # example xml:
    # <sequence name="preprocess">
    #     <step call="rotate" description="rotate stuff" prefix="img_">
    #         <argument value="90" />
    #     </step>
    #     <step call="ocr" description="rotate stuff" prefix="img_">
    #         <argument value="ocr_key" />
    #     </step>
    # </sequence>

    root = etree.Element("sequence",name=pipe.name)
    for step in pipe.pipe_steps:
        #root.append( etree.Element("step",call=step.call) )
        s = etree.SubElement(root, "step",call=step.call)
        for arg in step.args:
            s.append( etree.Element("argument",value=str(arg.arg))  )

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


def compose(*functions):
    """Compose list of functions

        Args:
            *functions: list of functions

        Returns:
            func: composed functions
    """
    return functools.reduce(lambda f, g: lambda x: f(g(x)), functions, lambda x: x)
