# -*- coding: utf-8 -*-
# © Toons

"""
Usage:
    delegate link [<secret>] [<2ndSecret>]
    delegate unlink
    delegate save <name>
    delegate status
    delegate voters
    delegate forged

Subcommands:
    link   : link to delegate using secret passphrases. If secret passphrases
             contains spaces, it must be enclosed within double quotes
             (ie "secret with spaces").
    unlink : unlink delegate.
    save   : encrypt account using pin code and save it localy.
    status : show information about linked delegate.
    voters : show voters contributions ([address - vote] pairs).
    forged : show forge report.
"""

import sys
import collections

from arky import rest
from arky.cli import DATA
from arky.cli.account import link as _link
from arky.utils.cli import prettyPrint


def _whereami():
	if DATA.account and not DATA.delegate:
		_loadDelegate()
	if DATA.delegate:
		return "delegate[%s]" % DATA.delegate["username"]

	return "delegate"


def _loadDelegate():
	if DATA.account:
		resp = rest.GET.api.delegates.get(publicKey=DATA.account["publicKey"], returnKey="delegate")
		if resp.get("publicKey", False):
			DATA.delegate = resp
			return True

		return False


def link(param):
	"""Link to delegate using secret passphrases"""
	_link(dict(param, **{"--escrow": False}))
	if not _loadDelegate():
		sys.stdout.write("Not a delegate\n")
		unlink()


def status():
	"""Show information about linked delegate"""
	if DATA.delegate:
		account = rest.GET.api.accounts(address=DATA.account["address"], returnKey="account")
		prettyPrint(dict(account, **DATA.delegate))


def unlink():
	"""Unlink delegate"""
	DATA.delegate.clear()


def forged():
	"""Show forge report"""
	if DATA.delegate:
		resp = rest.GET.api.delegates.forging.getForgedByAccount(generatorPublicKey=DATA.account["publicKey"])
		if resp.pop("success"):
			prettyPrint(dict([k, float(v) / 100000000] for k, v in resp.items()))


def voters():
	"""Show voters contributions"""
	if DATA.delegate:
		accounts = rest.GET.api.delegates.voters(publicKey=DATA.delegate["publicKey"]).get("accounts", [])
		sum_ = 0.
		log = collections.OrderedDict()
		for addr, vote in sorted([[c["address"], float(c["balance"]) / 100000000] for c in accounts], key=lambda e: e[-1]):
			log[addr] = "%.3f" % vote
			sum_ += vote
		log["%d voters" % len(accounts)] = "%.3f" % sum_
		prettyPrint(log)
