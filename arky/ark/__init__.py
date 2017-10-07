# -*- encoding: utf8 -*-
# © Toons

# __all__ = []

from .. import rest
from .. import cfg

from . import crypto

def init():
    network = rest.GET.api.loader.autoconfigure(returnKey="network")
    cfg.headers["version"] = network.pop("version")
    cfg.headers["nethash"] = network.pop("nethash")
    cfg.__dict__.update(network)
    cfg.fees = rest.GET.api.blocks.getFees(returnKey="fees")

def sendTransaction(**kw):
    tx = crypto.bakeTransaction(**kw)
    result = rest.POST.peer.transactions(transactions=[tx])
    return result
