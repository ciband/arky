# -*- encoding: utf8 -*-
# © Toons

import arky

__all__ = ["network", "account", "delegate", "ledger"]

from .. import __version__
from .. import HOME
from .. import ROOT
from .. import __FROZEN__
from .. import __PY3__
from .. import rest
from .. import util
from .. import cfg

import io
import os
import sys
import shlex
import docopt
import logging
import traceback
import threading

input = raw_input if not __PY3__ else input


class _Prompt(object):
	enable = True

	def __setattr__(self, attr, value):
		object.__setattr__(self, attr, value)

	def __repr__(self):
		return "%(hoc)s@%(net)s/%(wai)s> " % {
			"hoc": "hot" if cfg.hotmode else "cold",
			"net": cfg.network,
			"wai": self.module._whereami()
		}

	def state(self, state=True):
		_Prompt.enable = state

PROMPT = _Prompt()
PROMPT.module = sys.modules[__name__]


def _whereami():
	return ""


class Data(object):

	def __init__(self):
		self.initialize()

	def initialize(self):
		self.delegate = {}
		self.ledger = {}
		self.account = {}
		self.firstkeys = {}
		self.secondkeys = {}
		object.__setattr__(self, "executemode", False)
		object.__setattr__(self, "daemon", None)
		object.__setattr__(self, "escrowed", False)

	def __setattr__(self, attr, value):
		if attr == "daemon":
			if not isinstance(value, threading.Event):
				raise AttributeError("%s value must be a valid %s class" % (value, threading.Event))
			daemon = getattr(self, attr)
			if daemon:
				daemon.set()
		object.__setattr__(self, attr, value)

	def getCurrentAccount(self):
		return self.account if len(self.account) else \
	           self.ledger  if len(self.ledger)  else \
			   {}
		
	def getCurrentAddress(self):
		return self.getCurrentAccount().get("address", None)

	def getCurrentBalance(self):
		return float(self.getCurrentAccount().get("balance", 0))

	def getCurrent1stPKey(self):
		return self.getCurrentAccount().get("publicKey", None)

	def getCurrent2ndPKey(self):
		return self.getCurrentAccount().get("secondPublicKey", None)
		
DATA = Data()


def parse(argv):
	if argv[0] in __all__:
		module = getattr(sys.modules[__name__], argv[0])
		if hasattr(module, "_whereami"):
			PROMPT.module = module
			if len(argv) > 1:
				return parse(argv[1:])
		else:
			PROMPT.module = sys.modules[__name__]

	elif argv[0] in ["exit", ".."]:
		if PROMPT.module == sys.modules[__name__]:
			return False, False
		else:
			PROMPT.module = sys.modules[__name__]

	elif argv[0] == "EXIT":
		return False, False

	elif argv[0] in ["help", "?"]:
		sys.stdout.write("%s\n" % PROMPT.module.__doc__.strip())

	elif hasattr(PROMPT.module, argv[0]):
		try:
			arguments = docopt.docopt(PROMPT.module.__doc__, argv=argv)
		except:
			arguments = False
			sys.stdout.write("%s\n" % PROMPT.module.__doc__.strip())
		finally:
			return getattr(PROMPT.module, argv[0]), arguments

	else:
		sys.stdout.write("Command %s does not exist\n" % argv[0])

	return True, False


def snapLogging():
	logging.getLogger('requests').setLevel(logging.CRITICAL)
	logger = logging.getLogger()
	previous_logger_handler = logger.handlers.pop(0)
	logger.addHandler(
		logging.FileHandler(
			os.path.normpath(os.path.join(ROOT, __name__+".log")) if __FROZEN__ else \
			os.path.normpath(os.path.join(HOME, "."+__name__))
		)
	)
	return previous_logger_handler


def restoreLogging(handler):
	logging.getLogger('requests').setLevel(logging.INFO)
	logger = logging.getLogger()
	logger.handlers.pop(0)
	logger.addHandler(handler)


def start():
	_handler = snapLogging()

	sys.stdout.write(__doc__+"\n")
	_xit = False
	while not _xit:
		try:
			command = input(PROMPT)
		except EOFError:
			argv = ["EXIT"]
		else:
			argv = shlex.split(command)

		if len(argv) and _Prompt.enable:
			cmd, arg = parse(argv)
			if not cmd:
				_xit = True
			elif arg:
				if "link" not in argv:
					logging.info(command)
				else:
					logging.info(" ".join(argv[:2]+["x" * len(e) for e in ([] if len(argv) <= 2 else argv[2:])]))
				try:
					cmd(arg)
				except Exception as error:
					if hasattr(error, "__traceback__"):
						sys.stdout.write("".join(traceback.format_tb(error.__traceback__)).rstrip() + "\n")
					sys.stdout.write("%s\n" % error)
	
	if DATA.daemon:
		sys.stdout.write("Closing registry daemon...\n")
		DATA.daemon.set()

	restoreLogging(_handler)


def execute(*lines):
	DATA.executemode = True
	for line in lines:
		sys.stdout.write("%s%s\n" % (PROMPT, line))
		argv = shlex.split(line)
		if len(argv):
			cmd, arg = parse(argv)
			if cmd and arg:
				if "link" not in argv:
					logging.info(line)
				else:
					logging.info(" ".join(argv[:2]+["x" * len(e) for e in ([] if len(argv) <= 2 else argv[2:])]))
				try:
					cmd(arg)
				except Exception as error:
					if hasattr(error, "__traceback__"):
						sys.stdout.write("".join(traceback.format_tb(error.__traceback__)).rstrip() + "\n")
					sys.stdout.write("%s\n" % error)
	DATA.executemode = False


def launch(script):
	if os.path.exists(script):
		in_ = io.open(script)
		execute(*[l.strip() for l in in_.readlines()])
		in_.close()


def askYesOrNo(msg):
	if DATA.executemode:
		return True
	answer = ""
	while answer not in ["y", "Y", "n", "N"]:
		answer = input("%s [y-n]> " % msg)
	return False if answer in ["n", "N"] else True


def checkSecondKeys():
	secondPublicKey = DATA.account.get("secondPublicKey", False)
	if secondPublicKey and not DATA.secondkeys and not DATA.escrowed:
		secondKeys = arky.core.crypto.getKeys(util.hidenInput("Enter second passphrase: "))
		if secondKeys["publicKey"] == secondPublicKey:
			DATA.secondkeys = secondKeys
			return True
		else:
			sys.stdout.write("    Second public key missmatch...\n    Broadcast canceled\n")
			return False
	else:
		return True


def floatAmount(amount):
	account = DATA.account if len(DATA.account) else \
	          DATA.ledger  if len(DATA.ledger)  else \
			  {}
	if not account:
		return False

	if amount.endswith("%"):
		if DATA.executemode:
			balance = float(account.get("balance", 0.))
		else:
			resp = rest.GET.api.accounts.getBalance(address=account["address"])
			if resp["success"]:
				balance = float(resp["balance"])/100000000
			else:
				return False
		return float(amount[:-1])/100 * balance - cfg.fees["send"]/100000000.
	elif amount[0] in ["$", "€", "£", "¥"]:
		price = util.getTokenPrice(cfg.token, {"$":"usd", "EUR":"eur", "€":"eur", "£":"gbp", "¥":"cny"}[amount[0]])
		result = float(amount[1:])/price
		if askYesOrNo("%s=%s%f (%s/%s=%f) - Validate ?" % (amount, cfg.token, result, cfg.token, amount[0], price)):
			return result
		else:
			return False
	else:
		return float(amount)


def checkRegisteredTx(registry, folder=None, quiet=False):
	LOCK = None

	@util.setInterval(2*cfg.blocktime)
	def _checkRegisteredTx(registry):
		registered = util.loadJson(registry, folder)
		if not len(registered):
			if not quiet:
				sys.stdout.write("\nNo transaction remaining\n%s"%PROMPT)
			LOCK.set()
		else:
			if not quiet:
				sys.stdout.write("\n---\nTransaction registry check...\n")
			for tx_id, payload in list(registered.items()):
				if rest.GET.api.transactions.get(id=tx_id).get("success", False):
					registered.pop(tx_id)
				else:
					if not quiet:
						sys.stdout.write("Broadcasting transaction #%s\n" % tx_id)
					result = arky.core.sendPayload(payload)
					if not quiet:
						util.prettyPrint(result, log=False)
			
			util.dumpJson(registered, registry, folder)
			remaining = len(registered)
			if not remaining:
				if not quiet:
					sys.stdout.write("\nCheck finished, all transactions applied\n%s"%PROMPT)
				LOCK.set()
			elif not quiet:
				sys.stdout.write("\n%d transaction%s not applied in blockchain\nWaiting two blocks (%ds) before another broadcast...\n%s" % (remaining, "s" if remaining>1 else "", 2*cfg.blocktime, PROMPT))

	if not quiet:
		sys.stdout.write("Transaction check in two blocks (%ds)...\n" % (2*cfg.blocktime))
	LOCK = _checkRegisteredTx(registry)
	return LOCK


from . import network
from . import account
from . import delegate
from . import ledger

__doc__ = """Welcome to arky-cli [Python %(python)s / arky %(arky)s]
Available commands: %(sets)s""" % {"python": sys.version.split()[0], "arky":__version__, "sets": ", ".join(__all__)}
