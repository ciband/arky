# -*- coding: utf-8 -*-
# © Toons
import io
import os
import re
import sys
import json
import logging
import random
from importlib import import_module
from datetime import datetime

import pytz
import requests

from arky import __FROZEN__, cfg, ROOT


LOG = logging.getLogger(__name__)


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

class EndPoint(object):

	@staticmethod
	def _GET(*args, **kwargs):
		# API response contains several fields and wanted one can be extracted using
		# a returnKey that match the field name
		return_key = kwargs.pop('returnKey', False)
		peer = kwargs.pop('peer', False)
		peer = peer if peer else random.choice(cfg.peers)
		try:
			data = requests.get(
				peer + "/".join(args),
				params=dict([k.replace('and_', 'AND:'), v] for k,v in kwargs.items()),
				headers=cfg.headers,
				verify=cfg.verify,
				timeout=cfg.timeout
			).json()
		except Exception as error:
			data = {"success": False, "error": error, "peer": peer}
		else:
			if data.get("success") is True and return_key:
				data = data.get(return_key, {})
				if isinstance(data, dict):
					for item in ["balance", "unconfirmedBalance", "vote"]:
						if item in data:
							data[item] = float(data[item]) / 100000000
		return data

	@staticmethod
	def _POST(*args, **kwargs):
		peer = kwargs.pop("peer", False)
		peer = peer if peer else random.choice(cfg.peers)
		try:
			data = requests.post(
				peer + "/".join(args),
				data=json.dumps(kwargs),
				headers=cfg.headers,
				verify=cfg.verify,
				timeout=cfg.timeout
			).json()
		except Exception as error:
			data = {"success": False, "error": error, "peer": peer}
		return data

	@staticmethod
	def _PUT(*args, **kwargs):
		peer = kwargs.pop("peer", False)
		peer = peer if peer else random.choice(cfg.peers)
		try:
			data = requests.put(
				peer + "/".join(args),
				data=json.dumps(kwargs),
				headers=cfg.headers,
				verify=cfg.verify,
				timeout=cfg.timeout
			).json()
		except Exception as error:
			data = {"success": False, "error": error, "peer": peer}
		return data

	def __init__(self, elem=None, parent=None, method=None):
		if method not in [EndPoint._GET, EndPoint._POST, EndPoint._PUT]:
			raise Exception("REST method is not a valid one")
		self.elem = elem
		self.parent = parent
		self.method = method

	def __getattr__(self, attr):
		if attr not in ["elem", "parent", "method", "chain"]:
			if re.match("^_[0-9A-Fa-f].*", attr):
				attr = attr[1:]
			return EndPoint(attr, self, self.method)
		else:
			return object.__getattr__(self, attr)

	def __call__(self, **kwargs):
		return self.method(*self.chain(), **kwargs)

	def chain(self):
		return (self.parent.chain() + [self.elem]) if self.parent!=None else [""]

GET = EndPoint(method=EndPoint._GET)
POST = EndPoint(method=EndPoint._POST)
PUT = EndPoint(method=EndPoint._PUT)


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
	paht = os.path.join(ROOT, "net", network + ".net")
	if os.path.exists(paht):
		with io.open(os.path.join(ROOT, "net", network + ".net")) as f:
			data = json.load(f)
	else:
		raise Exception("File not found for {}".format(network))

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

	if len(cfg.peers):
		load(cfg.familly)
		cfg.network = network
		cfg.hotmode = True
	else:
		raise Exception("Error occurred during network setting...")
