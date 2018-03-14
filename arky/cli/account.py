# -*- encoding: utf8 -*-
# © Toons

"""
Usage:
    account link [<secret>] [<2ndSecret>|-e]
    account unlink
    account status
    account save <name>
    account register <username>
    account register 2ndSecret <secret>
    account register escrow <thirdparty>
    account validate [<registry>]
    account vote [-ud] [<delegates>]
    account send <amount> <address> [<message>]
    account wsend <amount> <weighting> [<message>]

Options:
-e --escrow  link as escrowed account
-u --up      up vote delegate name folowing
-d --down    down vote delegate name folowing

Subcommands:
    link     : link to account using secret passphrases. If secret passphrases
               contains spaces, it must be enclosed within double quotes
               (ie "secret with spaces").
    unlink   : unlink account.
    save     : encrypt account using pin code and save it localy.
    status   : show information about linked account.
    register : register linked account as delegate;
               or
               register second signature to linked account;
               or
               register an escrower using an account address or a publicKey.
    validate : validate transaction from registry.
    vote     : up or down vote delegate(s). <delegates> can be a coma-separated list
               or a valid new-line-separated file list conaining delegate names.
    send     : send token amount to address. You can set a 64-char message.
    wsend    : send token amount to multiple addresses using <weighting> json file
	           (address-weight pairs). You can set a 64-char message.
"""

import arky

from .. import HOME
from .. import cfg
from .. import rest
from .. import util

from . import DATA
from . import input
from . import checkSecondKeys
from . import checkRegisteredTx
from . import floatAmount
from . import askYesOrNo

import io
import os
import sys


def _send(payload):
	_address = DATA.getCurrentAddress()
	if DATA.escrowed:
		folder = os.path.join(HOME, ".escrow", cfg.network)
		if not os.path.exists(folder):
			os.makedirs(folder)
		sys.stdout.write("    Writing transaction...\n")
		registry_file = "%s.escrow" % (_address if _address else "thirdparty")
		registry = util.loadJson(registry_file, folder)
		if registry == {}:
			registry["secondPublicKey"] = DATA.getCurrent2ndPKey()
			registry["transactions"] = []
		payload.pop("id", None)
		registry["transactions"].extend([payload])
		util.dumpJson(registry, registry_file, folder)
	else:
		folder = os.path.join(HOME, ".registry", cfg.network)
		if not os.path.exists(folder):
			os.makedirs(folder)
		registry_file = "%s.registry" % (_address if _address else "thirdparty")
		registry = util.loadJson(registry_file, folder)
		typ_ = payload["type"]
		sys.stdout.write(("    Broadcasting transaction of %.8f %s to %s\n" % (payload["amount"] / 100000000, cfg.token, payload["recipientId"])) if typ_ == 0 else \
		                  "    Broadcasting vote...\n" if typ_ == 3 else \
						  "    Broadcasting transaction...\n")
		resp = arky.core.sendPayload(payload)
		util.prettyPrint(resp)
		if resp["success"]:
			registry[payload["id"]] = payload
			util.dumpJson(registry, registry_file, folder)
		DATA.daemon = checkRegisteredTx(registry_file, folder, quiet=True)


def _getVoteList(param):
	# get account votes
	voted = rest.GET.api.accounts.delegates(address=DATA.getCurrentAddress()).get("delegates", [])

	# if usernames is/are given
	if param["<delegates>"]:
		# try to load it from file if a valid path is given
		if os.path.exists(param["<delegates>"]):
			with io.open(param["<delegates>"]) as in_:
				usernames = [str(e) for e in in_.read().split() if e != ""]
		else:
			usernames = param["<delegates>"].split(",")

		voted = [d["username"] for d in voted]
		if param["--down"]:
			verb = "Down-vote"
			fmt = "-%s"
			to_vote = [username for username in usernames if username in voted]
		else:
			verb = "Up-vote"
			fmt = "+%s"
			to_vote = [username for username in usernames if username not in voted]

		return [fmt % pk for pk in util.getDelegatesPublicKeys(*to_vote)], verb, to_vote

	elif len(voted):
		util.prettyPrint(dict([d["username"], "%s%%" % d["approval"]] for d in voted))

	return [], "", []


def _whereami():
	if DATA.account:
		return "account[%s]" % util.shortAddress(DATA.getCurrent1stPKey() if DATA.escrowed else \
	                                             DATA.getCurrentAddress())
	else:
		return "account"


def link(param):
	unlink(param)

	if not param["<secret>"]:
		choices = util.findAccounts()
		if choices:
			name = util.chooseItem("Account(s) found:", *choices)
			try:
				data = util.loadAccount(util.createBase(util.hidenInput("Enter pin code: ")), name)
			except:
				sys.stdout.write("    Bad pin code...\n")
				return
			else:
				DATA.account = rest.GET.api.accounts(address=data["address"]).get("account", {})
				DATA.firstkeys = dict(publicKey=DATA.account["publicKey"], privateKey=data["privateKey"])
				if "secondPrivateKey" in data:
					DATA.secondkeys = dict(publicKey=DATA.account["secondPublicKey"], privateKey=data["secondPrivateKey"])
				_address = data["address"]
		else:
			sys.stdout.write("    No registered account found...\n")
			return

	else:
		DATA.firstkeys = arky.core.crypto.getKeys(param["<secret>"])
		_address = arky.core.crypto.getAddress(DATA.firstkeys["publicKey"])
		DATA.account = rest.GET.api.accounts(address=_address).get("account", {})

	if not DATA.account:
		sys.stdout.write("    %s does not exixt in %s blockchain...\n" % (_address, cfg.network))
	else:
		if param["<2ndSecret>"]:
			DATA.secondkeys = arky.core.crypto.getKeys(param["<2ndSecret>"])
			DATA.escrowed = False
		elif param["--escrow"]:
			if not DATA.account["secondPublicKey"]:
				sys.stdout.write("    Accound is not escrowed...\n")
				DATA.escrowed = False
			else:
				DATA.escrowed = True
		else:
			DATA.escrowed = False

		if not DATA.escrowed:
			DATA.daemon = checkRegisteredTx("%s.registry" % (DATA.account["address"]), os.path.join(HOME, ".registry", cfg.network), quiet=True)


def unlink(param):
	DATA.account.clear()
	DATA.delegate.clear()
	DATA.firstkeys.clear()
	DATA.secondkeys.clear()
	DATA.escrowed = False


def status(param):
	if DATA.account:
		util.prettyPrint(rest.GET.api.accounts(address=DATA.account["address"], returnKey="account"))


def save(param):
	if DATA.account:
		util.dumpAccount(
			util.createBase(util.hidenInput("Enter pin code: ")),
			DATA.account["address"],
			DATA.firstkeys["privateKey"],
			DATA.secondkeys.get("privateKey", None),
			param["<name>"]
		)


def register(param):

	if DATA.account:
		if param["2ndSecret"]:
			secondPublicKey = arky.core.crypto.getKeys(param["<secret>"])["publicKey"]
			if askYesOrNo("Register second public key %s ?" % secondPublicKey) \
			   and checkSecondKeys():
				sys.stdout.write("    Broadcasting second secret registration...\n")
				_send(arky.core.crypto.bakeTransaction(
					type=1,
					publicKey=DATA.firstkeys["publicKey"],
					privateKey=DATA.firstkeys["privateKey"],
					secondPrivateKey=DATA.secondkeys.get("privateKey", None),
					asset={"signature": {"publicKey": secondPublicKey}}
				))
		elif param["escrow"]:
			if DATA.account["secondPublicKey"]:
				sys.stdout.write("    This account can not be locked by thirdparty\n")
				return
			resp = rest.GET.api.accounts(address=param["<thirdparty>"])
			if resp["success"]:
				secondPublicKey = resp["account"]["publicKey"]
			else:
				secondPublicKey = arky.core.crypto.getKeys(param["<thirdparty>"])["publicKey"]
			if askYesOrNo("Register thirdparty public key %s ?" % secondPublicKey) \
			   and checkSecondKeys():
				sys.stdout.write("    Broadcasting thirdparty registration...\n")
				_send(arky.core.crypto.bakeTransaction(
					type=1,
					publicKey=DATA.firstkeys["publicKey"],
					privateKey=DATA.firstkeys["privateKey"],
					secondPrivateKey=DATA.secondkeys.get("privateKey", None),
					asset={"signature": {"publicKey": secondPublicKey}}
				))
		else:
			username = param["<username>"]
			if askYesOrNo("Register %s account as delegate %s ?" % (DATA.account["address"], username)) \
			   and checkSecondKeys():
				sys.stdout.write("    Broadcasting delegate registration...\n")
				_send(arky.core.crypto.bakeTransaction(
					type=2,
					publicKey=DATA.firstkeys["publicKey"],
					privateKey=DATA.firstkeys["privateKey"],
					secondPrivateKey=DATA.secondkeys.get("privateKey", None),
					asset={"delegate": {"username": username, "publicKey": DATA.firstkeys["publicKey"]}}
				))


def validate(param):
	unlink(param)

	if param["<registry>"]:
		registry = util.loadJson(param["<registry>"], os.path.join(HOME, ".escrow", cfg.network))
		if len(registry):
			thirdpartyKeys = arky.core.crypto.getKeys(util.hidenInput("Enter thirdparty passphrase: "))
			if registry["secondPublicKey"] == thirdpartyKeys["publicKey"]:
				items = []
				for tx in registry["transactions"]:
					if tx.get("asset", False):
						items.append("type=%(type)d, asset=%(asset)s" % tx)
					else:
						items.append("type=%(type)d, amount=%(amount)d, recipientId=%(recipientId)s" % tx)
				if not len(items):
					sys.stdout.write("    No transaction found in registry\n")
					return
				choices = util.chooseMultipleItem("Transactions(s) found:", *items)
				if askYesOrNo("Validate transactions %s ?" % ",".join([str(i) for i in choices])):
					for idx in choices:
						tx = registry["transactions"].pop(idx - 1)
						tx["signSignature"] = arky.core.crypto.getSignature(tx, thirdpartyKeys["privateKey"])
						tx["id"] = arky.core.crypto.getId(tx)
						_send(tx)
					util.dumpJson(registry, param["<registry>"], os.path.join(HOME, ".escrow", cfg.network))
				else:
					sys.stdout.write("    Validation canceled\n")
			else:
				sys.stdout.write("    Not the valid thirdparty passphrase\n")
		else:
			sys.stdout.write("    Transaction registry not found\n")

	if os.path.exists(os.path.join(HOME, ".registry", cfg.network, "thirdparty.registry")):
		DATA.daemon = checkRegisteredTx("thirdparty.registry", os.path.join(HOME, ".registry", cfg.network), quiet=False)


def vote(param):

	lst, verb, to_vote = _getVoteList(param)

	if len(lst) and askYesOrNo("%s %s ?" % (verb, ", ".join(to_vote))) \
				and checkSecondKeys():
		_send(arky.core.crypto.bakeTransaction(
			type=3,
			recipientId=DATA.account["address"],
			publicKey=DATA.firstkeys["publicKey"],
			privateKey=DATA.firstkeys["privateKey"],
			secondPrivateKey=DATA.secondkeys.get("privateKey", None),
			asset={"votes": lst}
		))


def send(param):

	if DATA.account:
		amount = floatAmount(param["<amount>"])
		if amount and askYesOrNo("Send %(amount).8f %(token)s to %(recipientId)s ?" % \
		                        {"token": cfg.token, "amount": amount, "recipientId": param["<address>"]}) \
		          and checkSecondKeys():
			_send(arky.core.crypto.bakeTransaction(
				amount=amount * 100000000,
				recipientId=param["<address>"],
				vendorField=param["<message>"],
				publicKey=DATA.firstkeys["publicKey"],
				privateKey=DATA.firstkeys["privateKey"],
				secondPrivateKey=DATA.secondkeys.get("privateKey", None)
			))


def wsend(param):

	if DATA.account:
		amount = floatAmount(param["<amount>"])
		weighting = util.loadJson(param["<weighting>"])

		try:
			checksum = sum(weighting.values())
			if checksum != 1.0:
				sys.stdout.write("    Bad weighting : checksum=%f (should be 1.0)\n" % checksum)
				return
		except:
			sys.stdout.write("    Not a valid weighting file\n")
			return

		util.prettyPrint(weighting)
		if amount and askYesOrNo("Send %(amount).8f %(token)s to %(recipientId)s addresses ?" % \
		                        {"token": cfg.token, "amount": amount, "recipientId": len(weighting)}) \
				  and checkSecondKeys():

			for address, weight in weighting.items():
				share = weight * amount
				if share * 100000000 > cfg.fees["send"]:
					_send(arky.core.crypto.bakeTransaction(
						amount=share * 100000000 - cfg.fees["send"],
						recipientId=address,
						vendorField=param["<message>"],
						publicKey=DATA.firstkeys["publicKey"],
						privateKey=DATA.firstkeys["privateKey"],
						secondPrivateKey=DATA.secondkeys.get("privateKey", None)
					))

			DATA.daemon = checkRegisteredTx("%s.registry" % (DATA.account["address"]), os.path.join(HOME, ".registry", cfg.network), quiet=True)
