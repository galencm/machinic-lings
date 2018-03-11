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
from lxml import etree
from textx.metamodel import metamodel_from_file
import roman

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

redis_conn = redis.StrictRedis(host=redis_ip, port=str(redis_port), decode_responses=True)
pubsub = redis_conn.pubsub()

def add_rule(dsl_string, expire=None):
    """
        Args:
            dsl_string(str): A string that using ruling grammar

        Returns:
            Tuple: name, key of created rule
    """

    if expire is None:
        expire = 0

    # unescape escaped newlines
    dsl_string = dsl_string.replace("\\n", "\n")
    logger.info("add rules from string: {}".format(repr(dsl_string)))
    try:
        rule = ruling_metamodel.model_from_str(dsl_string)
    except Exception as ex:
        logger.error("Failed to parse {} using {}".format(dsl_string, ruling_metamodel))
        logger.error(ex)
        return None, None
    logger.info("clearing existing: {}".format(rule.name))
    remove_rule(rule.name)
    dsl_hash = hashlib.sha224(dsl_string.encode()).hexdigest()
    rule_key = "rule:{}:{}".format(rule.name, dsl_hash)
    redis_conn.set(rule_key, dsl_string)
    logger.info("added rule: {}".format(rule_key))
    if expire > 0:
        redis_conn.expire(rule_key,expire)
        logger.info("expires in: {}".format(expire))
        logger.info("ttl: {}".format(redis_conn.ttl(rule_key)))

    return rule.name, rule_key

def remove_rule(name=None, dsl_string=None):
    """Match and remove rule(s) based on name, hashed contents or both

        Args:
            name(str): name of rule
            dsl_string(str): string following ruling grammar
    """
    if name is None and dsl_string is None:
        return

    if dsl_string is not None:
        dsl_hash = hashlib.sha224(dsl_string.encode()).hexdigest()
    else:
        dsl_hash = '*'

    if name is None or name is '':
        name="*"

    match_query = "rule:{}:{}".format(name, dsl_hash)
    rules = list(redis_conn.scan_iter(match=match_query))

    #do not pass empty list to redis
    if rules:
        redis_conn.delete(*rules)
        logger.info("removed rules(s) {}".format(rules))
    else:
        logger.info("no rules to remove matching {}".format(match_query))

def rule(name, glworb_key=None, glworb_dict=None, write_rulings=True):

    r = get_rule(name)
    glworb = {}

    if glworb_key:
        glworb.update(redis_conn.hgetall(glworb_key))

    if glworb_dict:
        glworb.update(glworb_dict)


    rulings = {}
    logger.info("rule: {} {}".format(name, r))

    # brittle handling:
    # for example: ~~ will not work on a range
    # types are handled using elif rather than
    # a more general method

    for ruleblock in r.ruleblocks:
        # each ruleblock will have to evaluate to true
        # based on evaluation of its contained rules
        local_results = []
        for rule in ruleblock.rules:
            if rule.field in glworb:
                field_value = glworb[rule.field]
                rule_value = rule.value.valuetype
                if rule.comparator == '==':
                    if field_value == rule_value:
                        local_results.append(True)
                    else:
                        local_results.append(False)
                elif rule.comparator == '~~':
                    if field_value.lower() == rule_value.lower():
                        local_results.append(True)
                    else:
                        local_results.append(False)
                elif rule.comparator == 'is':
                    # more robust way is to try to coerce to type
                    # from pydoc import locate
                    # if type(field_value) == type(locate(rule.value))
                    if rule_value == "str":
                        try:
                            str(field_value)
                            local_results.append(True)
                        except:
                            local_results.append(False)
                    elif rule_value == "roman":
                        try:
                            roman.fromRoman(field_value.upper())
                            local_results.append(True)
                        except:
                            local_results.append(False)
                    elif rule_value == "int":
                        try:
                            int(field_value)
                            local_results.append(True)
                        except:
                            local_results.append(False)
                elif rule.comparator == 'between':
                    if rule_value.range_start < int(field_value) < rule_value.range_end:
                        local_results.append(True)
                    else:
                        local_results.append(False)
                elif rule.comparator == 'contains':
                    if field_value.lower() in rule_value.lower():
                        local_results.append(True)
                    else:
                        local_results.append(False)
            else:
                local_results.append(False)

        if True in set(local_results) and len(set(local_results)) == 1:
            logger.info("rule applies")
            rulings.update({ruleblock.category : ruleblock.ruling})
            if write_rulings:
                logger.info("added field:value -> {}:{}".format(ruleblock.category, ruleblock.ruling))
                redis_conn.hmset(glworb_key, rulings)
        else:
            logger.info("rule does not apply")

    return rulings

def get_rules(query_pattern="*", raw=False, verbose=False):
    match_query = "rule:{}:*".format(query_pattern)
    rules = list(redis_conn.scan_iter(match=match_query))
    # rule:<name>:<contents hash>
    if verbose is False:
        rules = [s.split(":")[1] for s in rules]

    if raw is True:
        return rules
    else:
        logger.info(rules)
        return [get_rule(p) for p in rules if get_rule(p) is not None]

def get_rule(name, raw=False):

    if not name.startswith("rule:"):
        match_query = "rule:{}:*".format(name)
    else:
        match_query = "{}".format(name)

    logger.debug("match query: {}".format(match_query))
    logger.debug("matched rules: {}".format(str(list(redis_conn.scan_iter(match=match_query)))))

    try:
        rules = list(redis_conn.scan_iter(match=match_query))[0]
    except IndexError as ex:
        logger.debug(ex)
        return None

    stored_rule = redis_conn.get(rules)
    #logger.info(match_query)
    if stored_rule:
        try:
            rule = ruling_metamodel.model_from_str(stored_rule)
            if raw is True:
                return stored_rule
            else:
                return rule
        except Exception as ex:
            logger.warn(ex)
            return None

def rule_xml2str(xml=None, raw=False):
    # limitations:
    #
    #   currently works with single rule instead of
    #   rules inside of a ruleset <ruleset name=> </ruleset>
    #
    #   ruleset name is either an attribute or hash of rule_string
    #   if 'ruleset' attribute does not exist
    #
    #   also only uses a single parameter child
    #
    #   {result} is only quoted string in rule_string

    # sample xml:
    #   <rule source="chapter" destination="chapter" result="chapter1">
    #       <parameter symbol="is" values="int" />
    #   </rule>

    # sample dsl:
    #   ruleset bar {
    #   method ~~ "slurp_gphoto2"
    #   -> action "slurped"

    #   chapter_ocr ~~ "Getting Started" 
    #   -> chapter "chapter2"

    #   page_num_ocr is int -> pagenumbering "numeral"

    #   page_num_ocr between  1,12 -> chapter "chapter1"
    #   }

    xml_hash = hashlib.sha224(xml.encode()).hexdigest()
    rule_xml = etree.fromstring(xml)
    rule_attributes = {"source" : "",
                       "symbol":"",
                       "values":"",
                       "destination":"",
                       "result":""}
    rule_attributes["source"] = rule_xml.get("source")
    rule_attributes["destination"] = rule_xml.get("destination")
    rule_attributes["result"] = rule_xml.get("result")
    rule_attributes["ruleset"] = rule_xml.get("ruleset")
    if rule_attributes["ruleset"] is None:
        # prepend sha with 'r' for textx metamodel ID
        rule_attributes["ruleset"] = "r" + xml_hash
    for child in rule_xml:
        if child.tag == "parameter":
            try:
                rule_attributes["symbol"] = child.get("symbol")
                rule_attributes["values"] = child.get("values")
            except KeyError:
                pass
    rule_string = ""
    rule_string += "ruleset {ruleset} {{\n".format(**rule_attributes)
    rule_string += '{source} {symbol} {values} -> {destination} "{result}"\n'.format(**rule_attributes)
    rule_string += "}"
    return rule_string

def rule_str2xml(dsl_string=None, name=None, raw=False, file=None):
    # placeholder
    # revise gsl model xml for ruling
    pass
