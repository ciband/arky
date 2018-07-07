# -*- coding: utf-8 -*-
# © Toons
"""
Available commands: network, account, delegate, ledger
"""
import io
import os
import sys
import shlex
import logging
import traceback
import threading

from importlib import import_module
from builtins import input

import docopt

from six import PY3

import arky
from arky import __version__, __FROZEN__, HOME, ROOT, rest, cfg
from arky.exceptions import ParserException
from arky.utils.http import getTokenPrice
from arky.utils.decorators import setInterval
from arky.utils.cli import hidenInput, prettyPrint
from arky.utils.data import loadJson, dumpJson

PACKAGES = ['network', 'account', 'delegate', 'ledger']


def _whereami():
	return ""

def start():
	CLI().start()


class CLI:

	def __init__(self):
		self.enabled = True
		self.module = sys.modules[__name__]

	@property
	def prompt(self):
		"""
		Prompt showing current location in the CLI
		"""
		return "{hoc}@{net}/{wai}> ".format(
			hoc="hot" if cfg.hotmode else "cold",
			net=cfg.network,
			wai=self.module._whereami()
		)

	def start(self, msg=None):
		"""
		Start an interactive CLI
		"""
		_handler = snapLogging()
		sys.stdout.write(
			'Welcome to arky-cli [Python %(python)s / arky %(arky)s]\n' % {
				"python": sys.version.split()[0],
				"arky": __version__,
			} if not msg else msg
		)
		sys.stdout.write("%s\n" % self.module.__doc__.strip())

		while True:
			try:
				command = input(self.prompt)
			except ParserException as error:
				sys.stdout.write("%s\n" % error)
				argv = [".."]
			except EOFError:
				argv = ["EXIT"]
			else:
				argv = shlex.split(command)

			if len(argv) and self.enabled:
				cmd, arg = self.parse(argv)
				if not cmd:
					break
				elif arg:
					if "link" not in argv:
						logging.info(command)
					else:
						command = censorship(argv)
						logging.info(command)
					try:
						cmd(arg)
					except ParserException as error:
						# pass because we already log the exception when calling `self.prompt`
						pass
					except Exception as error:
						if hasattr(error, "__traceback__"):
							sys.stdout.write("".join(traceback.format_tb(error.__traceback__)).rstrip() + "\n")
						sys.stdout.write("%s\n" % error)

		if DATA.daemon:
			sys.stdout.write("Closing registry daemon...\n")
			DATA.daemon.set()
		restoreLogging(_handler)

	def parse(self, argv):
		"""
		Parses given list of argvs

		Args:
			argv (list): list of arguments

		Returns:
			tuple: tuple containing two parts, first one is a command and the second and argument
		"""
		if argv[0] in PACKAGES:
			module = getattr(sys.modules[__name__], argv[0], None)
			if not module:
				module = import_module("arky.cli.{0}".format(argv[0]))
			if hasattr(module, "_whereami"):
				self.module = module
				if len(argv) > 1:
					return self.parse(argv[1:])
			else:
				logging.error('Module %s does not have a defined _whereami function', argv[0])

		elif argv[0] in ["exit", ".."]:
			if self.module.__name__ == 'arky.cli':
				return False, False
			else:
				self.module = sys.modules[__name__]

		elif argv[0] == "EXIT":
			return False, False

		elif argv[0] in ["help", "?"]:
			sys.stdout.write("%s\n" % self.module.__doc__.strip())

		elif hasattr(self.module, argv[0]):
			try:
				arguments = docopt.docopt(self.module.__doc__, argv=argv)
			except:
				arguments = False
				sys.stdout.write("%s\n" % self.module.__doc__.strip())
			return getattr(self.module, argv[0]), arguments

		else:
			sys.stdout.write("Command %s does not exist\n" % argv[0])

		return True, False


class Data(object):

	def __init__(self):
		object.__setattr__(self, "executemode", False)
		object.__setattr__(self, "daemon", None)
		self.initialize()

	def initialize(self):
		self.delegate = {}
		self.ledger = {}
		self.account = {}
		self.firstkeys = {}
		self.secondkeys = {}
		self.escrowed = False

	def __setattr__(self, attr, value):
		if attr == "daemon":
			if PY3:
				is_threading = isinstance(value, threading.Event)
			else:
				# py2 doesn't support Event object in isinstance
				is_threading = value.__module__ == 'threading'

			if not is_threading:
				raise AttributeError("%s value must be a valid %s class" % (value, threading.Event))

			daemon = getattr(self, attr)
			if daemon:
				daemon.set()
		object.__setattr__(self, attr, value)

	def getCurrentAccount(self):
		if self.account:
			account = self.account
		elif self.ledger:
			account = self.ledger
		else:
			account = {}
		return account

	def getCurrentAddress(self):
		return self.getCurrentAccount().get("address", None)

	def getCurrentBalance(self):
		return float(self.getCurrentAccount().get("balance", 0))

	def getCurrent1stPKey(self):
		return self.getCurrentAccount().get("publicKey", None)

	def getCurrent2ndPKey(self):
		return self.getCurrentAccount().get("secondPublicKey", None)


DATA = Data()


def snapLogging():
	logging.getLogger('requests').setLevel(logging.CRITICAL)
	logger = logging.getLogger()
	previous_logger_handler = logger.handlers.pop(0)
	if __FROZEN__:
		filepath = os.path.normpath(os.path.join(ROOT, "cli.log"))
	else:
		filepath = os.path.normpath(os.path.join(HOME, "." + __name__))
	logger.addHandler(logging.FileHandler(filepath))
	return previous_logger_handler


def restoreLogging(handler):
	logging.getLogger('requests').setLevel(logging.INFO)
	logger = logging.getLogger()
	logger.handlers.pop(0)
	logger.addHandler(handler)


def execute(lines):
	"""
	Executes command given line by line

	Args:
		lines: list of commands to execute
	"""
	DATA.executemode = True
	snapLogging()
	cli = CLI()
	for line in lines:
		sys.stdout.write("%s%s\n" % (cli.prompt, line))
		argv = shlex.split(line)
		if len(argv):
			cmd, arg = cli.parse(argv)
			if cmd and arg:
				if "link" not in argv:
					logging.info(line)
				else:
					line = censorship(argv)
					logging.info(line)
				try:
					cmd(arg)
				except Exception as error:
					if hasattr(error, "__traceback__"):
						sys.stdout.write("".join(traceback.format_tb(error.__traceback__)).rstrip() + "\n")
					sys.stdout.write("%s\n" % error)
	DATA.executemode = False


def launch(script):
	"""
	Script launcher that executed a given script

	Args:
		script (string): path of the script that we want to execute
	"""
	if os.path.exists(script):
		with io.open(script, "rb") as file:
			lines = [l.strip().decode("utf-8") for l in file.readlines()]
			execute(lines)


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
		secondKeys = arky.core.crypto.getKeys(hidenInput("Enter second passphrase: "))
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
			balance = float(account.get("balance", 0.)) / 100000000
		else:
			resp = rest.GET.api.accounts.getBalance(address=account["address"])
			if resp["success"]:
				balance = float(resp["balance"]) / 100000000
			else:
				return False
		return float(amount[:-1]) / 100 * balance - cfg.fees["send"] / 100000000.
	elif amount[0] in ["$", "€", "£", "¥"]:
		price = getTokenPrice(cfg.token, {"$": "usd", "EUR": "eur", "€": "eur", "£": "gbp", "¥": "cny"}[amount[0]])
		result = float(amount[1:]) / price
		if askYesOrNo("%s=%s%f (%s/%s=%f) - Validate ?" % (amount, cfg.token, result, cfg.token, amount[0], price)):
			return result
		else:
			return False
	else:
		return float(amount)


def checkRegisteredTx(registry, folder=None, quiet=False):
	LOCK = None

	@setInterval(2 * cfg.blocktime)
	def _checkRegisteredTx(registry):
		registered = loadJson(registry, folder)
		if not len(registered):
			if not quiet:
				sys.stdout.write("\nNo transaction remaining\n")
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
						prettyPrint(result, log=False)

			dumpJson(registered, registry, folder)
			remaining = len(registered)
			if not remaining:
				if not quiet:
					sys.stdout.write("\nCheck finished, all transactions applied\n")
				LOCK.set()
			elif not quiet:
				sys.stdout.write("\n%d transaction%s not applied in blockchain\nWaiting two blocks (%ds) before another broadcast...\n" % (remaining, "s" if remaining > 1 else "", 2 * cfg.blocktime))

	if not quiet:
		sys.stdout.write("Transaction check in two blocks (%ds)...\n" % (2 * cfg.blocktime))
	LOCK = _checkRegisteredTx(registry)
	return LOCK


def censorship(argv):
	"""
	Censors any delicate information from a given command arguments
	"""
	return " ".join(argv[:2] + ["x" * len(e) for e in ([] if len(argv) <= 2 else argv[2:])])
