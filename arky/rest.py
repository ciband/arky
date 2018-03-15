# -*- encoding: utf8 -*-
# © Toons
import io
import os
import sys
import json
import pytz
import logging
import random
import requests

from importlib import import_module
from datetime import datetime
from arky import __FROZEN__, cfg, ROOT


LOG = logging.getLogger(__name__)


#################
#  API methods  #
#################

def get(entrypoint, **kwargs):
    """
    Generic GET call using requests lib. It returns server response as dict object.
    It randomly select one of peers registered in cfg.peers list. A custom peer can
    be used.

    Argument:
    entrypoint (str) -- entrypoint url path

    Keyword argument:
    **kwargs -- api parameters as keyword argument

    Return dict
    """
    # API response contains several fields and wanted one can be extracted using
    # a returnKey that match the field name
    return_key = kwargs.pop('returnKey', False)
    peer = kwargs.pop('peer', False)

    params = {}
    for key, val in kwargs.items():
        params[key.replace('and_', 'AND:')] = val

    peer = peer if peer else random.choice(cfg.peers)

    try:
        response = requests.get(
            '{0}{1}'.format(peer, entrypoint),
            params=params,
            headers=cfg.headers,
            verify=cfg.verify,
            timeout=cfg.timeout
        )
        data = response.json()
    except Exception as error:
        data = {"success": False, "error": error, "peer": peer}
    else:
        # if not data.get("success"):
        #     return data
        if return_key:
            data = data[return_key]

            if isinstance(data, dict):
                for item in ["balance", "unconfirmedBalance", "vote"]:
                    if item in data:
                        data[item] = float(data[item]) / 100000000
    return data


def post(entrypoint, **kwargs):
    """
    Generic post call using requests lib. It returns server response as dict object.
    It randomly select one of peers registered in cfg.peers list. A custom peer can
    be used.

    Argument:
    entrypoint (str) -- entrypoint url path

    Keyword argument:
    **kwargs -- api parameters as keyword argument

    Return dict
    """
    peer = kwargs.pop("peer", False)
    payload = kwargs
    peer = peer if peer else random.choice(cfg.peers)
    try:
        response = requests.post(
            '{0}{1}'.format(peer, entrypoint),
            data=json.dumps(payload),
            headers=cfg.headers,
            verify=cfg.verify,
            timeout=cfg.timeout
        )
        data = response.json()
    except Exception as error:
        data = {"success": False, "error": error}
    return data


def put(entrypoint, **kwargs):
    """
    Generic PUT call using requests lib. It returns server response as dict object.
    It randomly select one of peers registered in cfg.peers list. A custom peer can
    be used.

    Argument:
    entrypoint (str) -- entrypoint url path

    Keyword argument:
    **kwargs -- api parameters as keyword argument

    Return dict
    """
    peer = kwargs.pop("peer", False)
    payload = kwargs
    peer if peer else random.choice(cfg.peers)
    try:
        response = requests.put(
            '{0}{1}'.format(peer, entrypoint),
            data=json.dumps(payload),
            headers=cfg.headers,
            verify=cfg.verify,
            timeout=cfg.timeout
        )
        data = response.json()
    except Exception as error:
        data = {"success": False, "error": error}
    return data


def check_latency(peer):
    """
    Returns latency in second for a given peer
    """
    try:
        request = requests.get(peer, timeout=cfg.timeout, verify=cfg.verify)
    except Exception:
        # we want to capture all exceptions because we don't want to stop checking latency for
        # other peers that might be working
        return
    return request.elapsed.total_seconds()


#################
#  API wrapper  #
#################

class Endpoint(object):

    def __init__(self, method, endpoint):
        self.method = method
        self.endpoint = endpoint

    def __call__(self, **kw):
        return self.method(self.endpoint, **kw)

    @staticmethod
    def createEndpoint(ndpt, method, path):
        newpath = ""
        for name in path.split("/"):
            if not name:
                continue
            newpath += "/" + name
            if not hasattr(ndpt, name):
                setattr(ndpt, name, Endpoint(method, newpath))
            ndpt = getattr(ndpt, name)


def load_endpoints(network):
    global POST, PUT, GET

    try:
        with io.open(os.path.join(ROOT, "ndpt", network + ".ndpt")) as f:
            endpoints = json.load(f)
    except IOError:
        LOG.debug('No endpoints file found for %s', network)
        return False

    POST = Endpoint(post, "")
    for endpoint in endpoints["POST"]:
        POST.createEndpoint(POST, post, endpoint)

    PUT = Endpoint(put, "")
    for endpoint in endpoints["PUT"]:
        PUT.createEndpoint(PUT, put, endpoint)

    GET = Endpoint(get, "")
    for endpoint in endpoints["GET"]:
        GET.createEndpoint(GET, get, endpoint)

    return True


#######################
#  network selection  #
#######################

def load(family_name):
    """
    Loads a given blockchain family's functions into `arky.core` modules
    """

    try:
        # try to stop DAEMON_PEERS from a previous use of ark blockchain family
        sys.modules[__package__].core.DAEMON_PEERS.set()
    except AttributeError:
        pass

    # loads blockchain family package into as arky core
    sys.modules[__package__].core = import_module('arky.{0}'.format(family_name))
    try:
        # initialize blockchain familly package
        sys.modules[__package__].core.init()
    except AttributeError:
        raise Exception("%s package is not a valid blockchain family" % family_name)

    try:
        # delete real package name loaded (to keep namespace clear)
        sys.modules[__package__].__delattr__(family_name)
    except AttributeError:
        pass


def use(network, **kwargs):
    """
    Loads rest api endpoints from a ndpt file, sets the attributes in the `cfg` module and triggers
    a `load` function which loads a given blockchain family's functions into `arky.core` modules
    """
    # clear data in cfg module and initialize with minimum vars
    cfg.__dict__.clear()
    cfg.network = None
    cfg.hotmode = False

    try:
        # clean previous loaded modules with network name
        sys.modules[__package__].__delattr__(network)
    except AttributeError:
        pass

    with io.open(os.path.join(ROOT, "net", network + ".net")) as f:
        data = json.load(f)

    data.update(**kwargs)

    # save json data as variables in cfg.py module and set verify (for ssl) and begin time because
    # blockchain can use different begin times
    cfg.__dict__.update(data)
    cfg.verify = os.path.join(os.path.dirname(sys.executable), 'cacert.pem') if __FROZEN__ else True
    cfg.begintime = datetime(*cfg.begintime, tzinfo=pytz.UTC)

    if data.get("seeds", []):
        cfg.peers = []
        for seed in data["seeds"]:
            if check_latency(seed):
                cfg.peers.append(seed)
                break
    else:
        for peer in data.get("peers", []):
            peer = "http://{0}:{1}".format(peer, data.get("port", 22))
            if check_latency(peer):
                cfg.peers = [peer]
                break

    # if endpoints found, create them and update network
    if len(cfg.peers) and load_endpoints(cfg.endpoints):
        load(cfg.familly)
        cfg.network = network
        cfg.hotmode = True
    else:
        raise Exception("Error occurred during network setting...")
