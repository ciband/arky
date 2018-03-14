# -*- encoding: utf8 -*-
# © Toons

"""
Usage:
    ledger link [-i <index> -r <rank>]
    ledger unlink
    ledger status
    ledger send <amount> <address> [<message>]
    ledger vote [-ud] [<delegates>]

Options:
-i <index> --account-index <index>  ledger account index  [default: 0]
-r <rank> --address-rank <rank>     ledger address rank   [default: 0]
-u --up                             up vote delegate name folowing
-d --down                           down vote delegate name folowing

Subcommands:
    link     : link to ledger account.
    status   : show information about linked account.
    send     : send token amount to <address>. You can set a 64-char message.
    vote     : up or down vote delegate(s). <delegates> can be a coma-separated list
               or a valid new-line-separated file list conaining delegate names.
"""
#   ledger validate <registry>
#   validate : validate transaction from registry.

from .. import HOME
from .. import rest
from .. import cfg
from .. import util
from .. import ldgr
from .. import slots

from . import DATA
from . import input
from . import floatAmount
from . import askYesOrNo

from .account import _send
from .account import _getVoteList

import traceback
import arky
import sys
import os

from arky.exceptions import ParserException


def _sign(tx, derivation_path):
	try:
		tx = ldgr.signTx(tx, derivation_path, debug=True)
	except Exception as e:
		if not len(e.__dict__):
			sys.stdout.write("%r\n" % e)
		elif e.sw == 28416:
			sys.stdout.write("Ledger key is not ready, try again...\n")
		elif e.sw == 27013:
			sys.stdout.write("Transaction canceled\n")
		else:
			sys.stdout.write("".join(traceback.format_tb(e.__traceback__)).rstrip() + "\n")
			sys.stdout.write("%r\n" % e)
	else:
		return tx

	return False


def _whereami():
	if hasattr(cfg, "slip44"):
		if DATA.ledger:
			return "ledger[%s]" % util.shortAddress(DATA.ledger["address"])
		else:
			return "ledger"
	else:
		raise ParserException('Ledger not available on {} network'.format(cfg.network))


def link(param):
	if hasattr(cfg, "slip44"):

		ledger_dpath = "44'/" + cfg.slip44 + "'/%(--account-index)s'/0/%(--address-rank)s" % param
		try:
			publicKey = ldgr.getPublicKey(ldgr.parseBip32Path(ledger_dpath))
			address = arky.core.crypto.getAddress(publicKey)
			DATA.ledger = rest.GET.api.accounts(address=address).get("account", {})
		except:
			sys.stdout.write("Ledger key is not ready, try again...\n")
		else:
			if not DATA.ledger:
				sys.stdout.write("    %s account does not exixts in %s blockchain...\n" % (address, cfg.network))
			else:
				DATA.ledger["path"] = ledger_dpath

	else:
		raise ParserException('Ledger not available on {} network'.format(cfg.network))


def status(param):
	if DATA.ledger:
		data = rest.GET.api.accounts(address=DATA.ledger["address"], returnKey="account")
		data["derivationPath"] = DATA.ledger["path"]
		util.prettyPrint(data)


def unlink(param):
	DATA.ledger.clear()


def send(param):

	if DATA.ledger:
		amount = floatAmount(param["<amount>"])
		if amount:
			sys.stdout.write("Use ledger key to confirm or or cancel :\n")
			sys.stdout.write("    Send %(amount).8f %(token)s to %(recipientId)s ?\n" % \
		                    {"token": cfg.token, "amount": amount, "recipientId": param["<address>"]})
			tx = dict(
				type=0,
				timestamp=int(slots.getTime()),
				fee=cfg.fees["send"],
				amount=int(amount * 100000000),
				recipientId=param["<address>"],
				vendorField=param["<message>"],
			)

			if _sign(tx, DATA.ledger["path"]): _send(tx)


def vote(param):

	lst, verb, to_vote = _getVoteList(param)

	if len(lst):
		sys.stdout.write("Use ledger key to confirm or or cancel :\n")
		sys.stdout.write("    %s %s ?\n" % (verb, ", ".join(to_vote)))
		tx = dict(
			type=3,
			timestamp=int(slots.getTime()),
			fee=cfg.fees["vote"],
			amount=0,
			recipientId=DATA.ledger["address"],
			asset={"votes": lst}
		)

		if _sign(tx, DATA.ledger["path"]): _send(tx)


# def validate(param):
# 	unlink(param)
# 	if param["<registry>"]:
# 		folder = os.path.join(HOME, ".escrow", cfg.network)
# 		registry = util.loadJson(param["<registry>"], folder)

# 		if len(registry):

# 			derivation_path = input("Enter the derivation path: ")
# 			try:
# 				public_key = ldgr.getPublicKey(ldgr.parseBip32Path(derivation_path))
# 			except Exception as e:
# 				public_key = ""
# 				sys.stdout.write("%r\n" % e)
# 				return False

# 			if registry["secondPublicKey"] == public_key:
# 				items = []
# 				for tx in registry["transactions"]:
# 					if tx.get("asset", False):
# 						items.append("type=%(type)d, asset=%(asset)s" % tx)
# 					else:
# 						items.append("type=%(type)d, amount=%(amount)d, recipientId=%(recipientId)s" % tx)
# 				if not len(items):
# 					sys.stdout.write("    No transaction found in registry\n")
# 					return
# 				choices = util.chooseMultipleItem("Transactions(s) found:", *items)
# 				if askYesOrNo("Validate transactions %s ?" % ",".join([str(i) for i in choices])):
# 					for idx in list(choices):
# 						tx = registry["transactions"][idx-1]
# 						if _sign(tx, derivation_path):
# 							_send(tx)
# 							registry["transactions"].pop(idx-1)
# 					util.dumpJson(registry, param["<registry>"], folder)
# 				else:
# 					sys.stdout.write("    Validation canceled\n")
# 			else:
# 				sys.stdout.write("    Not the valid thirdparty passphrase\n")
# 		else:
# 			sys.stdout.write("    Transaction registry not found\n")
