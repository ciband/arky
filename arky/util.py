# -*- encoding: utf8 -*-
# © Toons

from . import __PY3__
from . import HOME
from . import ROOT
from . import slots
from . import rest
from . import cfg

import io
import os
import sys
import json
import struct
import hashlib
import logging
import getpass
import binascii
import requests
import threading

##############
## bin util ##
##############

# byte as int conversion
basint = (lambda e:e) if __PY3__ else \
         (lambda e:ord(e))
# read value as binary data from buffer
unpack =  lambda fmt, fileobj: struct.unpack(fmt, fileobj.read(struct.calcsize(fmt)))
# write value as binary data into buffer
pack = lambda fmt, fileobj, value: fileobj.write(struct.pack(fmt, *value))
# read bytes from buffer
unpack_bytes = lambda f,n: unpack("<"+"%ss"%n, f)[0]
# write bytes into buffer
pack_bytes = (lambda f,v: pack("!"+"%ss"%len(v), f, (v,))) if __PY3__ else \
             (lambda f,v: pack("!"+"c"*len(v), f, v))


def hexlify(data):
	result = binascii.hexlify(data)
	return str(result.decode() if isinstance(result, bytes) else result)


def unhexlify(data):
	if len(data)%2: data = "0"+data
	result = binascii.unhexlify(data)
	return result if isinstance(result, bytes) else result.encode()


###############
## http util ##
###############

def getTokenPrice(token, fiat="usd"):
	cmc_ark = json.loads(requests.get(
		"https://api.coinmarketcap.com/v1/ticker/"+token+"/?convert="+fiat.upper(),
		verify=cfg.verify
	).text)
	try: return float(cmc_ark[0]["price_%s"%fiat.lower()])
	except: return 0.
	

def getCandidates():
	candidates = []
	req = rest.GET.api.delegates(offset=len(candidates), limit=cfg.delegate).get("delegates", [])
	while not len(req) < cfg.delegate:
		candidates.extend(req)
		req = rest.GET.api.delegates(offset=len(candidates), limit=cfg.delegate).get("delegates", [])
	candidates.extend(req)
	return candidates


def getDelegatesPublicKeys(*usernames):
	return [c["publicKey"] for c in getCandidates() if c["username"] in usernames]


def getTransactions(timestamp=0, **param):
	param.update(returnKey="transactions", limit=cfg.maxlimit, orderBy="timestamp:desc")
	txs = rest.GET.api.transactions(**param)
	if isinstance(txs, list) and len(txs):
		while txs[-1]["timestamp"] >= timestamp:
			param.update(offset=len(txs))
			search = rest.GET.api.transactions(**param)
			txs.extend(search)
			if len(search) < cfg.maxlimit:
				break
	elif not len(txs):
		raise Exception("Address has null transactions.")
	else:
		raise Exception(txs.get("error", "Api error"))
	return sorted([t for t in txs if t["timestamp"] >= timestamp], key=lambda e:e["timestamp"], reverse=True)


def getHistory(address, timestamp=0):
	return getTransactions(timestamp, recipientId=address, senderId=address)


def getVoteForce(address, **kw):
	# determine timestamp
	balance = kw.pop("balance", 0)/100000000.
	if not balance:
		balance = float(rest.GET.api.accounts.getBalance(address=address, returnKey="balance"))/100000000.
	delta = slots.datetime.timedelta(**kw)
	if delta.total_seconds() < 86400:
		return balance
	now = slots.datetime.datetime.now(slots.pytz.UTC)
	timestamp_limit = slots.getTime(now - delta)
	# get transaction history
	history = getHistory(address, timestamp_limit)
	# if no transaction over periode integrate balance over delay and return it
	if not history:
		return balance*delta.total_seconds()/3600
	# else
	end = slots.getTime(now)
	sum_ = 0.
	brk = False
	for tx in history:
		delta_t = (end - tx["timestamp"])/3600
		sum_ += balance * delta_t
		balance += ((tx["fee"]+tx["amount"]) if tx["senderId"] == address else -tx["amount"])/100000000.
		if tx["type"] == 3:
			brk = True
			break
		end = tx["timestamp"]
	if not brk:
		sum_ += balance * (end - timestamp_limit)/3600
	return sum_


##############
## def util ##
##############

def setInterval(interval):
	""" threaded decorator
	>>> @setInterval(10)
	... def tick(): print("Tick")
	>>> stop = tick() # print 'Tick' every 10 sec
	>>> type(stop)
	<class 'threading.Event'>
	>>> stop.set() # stop printing 'Tick' every 10 sec
	"""
	def decorator(function):
		def wrapper(*args, **kwargs):
			stopped = threading.Event()
			def loop(): # executed in another thread
				while not stopped.wait(interval): # until stopped
					# print("%r executed !"%function)
					function(*args, **kwargs)
				# print("loop on %r stopped..." % function)
			t = threading.Thread(target=loop)
			t.daemon = True # stop if the program exits
			t.start()
			return stopped
		return wrapper
	return decorator


def shortAddress(addr, sep="...", n=5):
	return addr[:n]+sep+addr[-n:]


def prettyfy(dic, tab="    "):
	result = ""
	if len(dic):
		maxlen = max([len(e) for e in dic.keys()])
		for k,v in dic.items():
			if isinstance(v, dict):
				result += tab + "%s:" % k.ljust(maxlen)
				result += prettyfy(v, tab*2)
			else:
				result += tab + "%s: %s" % (k.rjust(maxlen),v)
			result += "\n"
		return result.encode("ascii", errors="replace").decode()


def prettyPrint(dic, tab="    ", log=True):
	pretty = prettyfy(dic, tab)
	if len(dic):
		sys.stdout.write(pretty.decode() if isinstance(pretty, bytes) else pretty)
		if log: logging.info("\n"+pretty.rstrip())
	else:
		sys.stdout.write("%sNothing to print here\n" % tab)
		if log: logging.info("%sNothing to log here" % tab)


def dumpJson(cnf, name, folder=None):
	filename = os.path.join(HOME if not folder else folder, name)
	out = io.open(filename, "w" if __PY3__ else "wb")
	json.dump(cnf, out, indent=2)
	out.close()
	return os.path.basename(filename)


def loadJson(name, folder=None):
	filename = os.path.join(HOME if not folder else folder, name)
	if os.path.exists(filename):
		in_ = io.open(filename)
		data = json.load(in_)
		in_.close()
		return data
	else:
		return {}


def popJson(name, folder=None):
	filename = os.path.join(HOME if not folder else folder, name)
	if os.path.exists(filename):
		os.remove(filename)


def findNetworks():
	try:
		return [os.path.splitext(name)[0] for name in os.listdir(os.path.join(ROOT, "net")) if name.endswith(".net")]
	except:
		return []


def chooseMultipleItem(msg, *elem):
	n = len(elem)
	if n > 0:
		sys.stdout.write(msg + "\n")
		for i in range(n):
			sys.stdout.write("    %d - %s\n" % (i+1, elem[i]))
		indexes = []
		while len(indexes) == 0:
			try:
				indexes = input("Choose items: [1-%d or all]> " % n)
				if indexes == "all":
					indexes = [i+1 for i in range(n)]
				else:
					indexes = [int(s) for s in indexes.strip().replace(" ", ",").split(",") if s != ""]
					indexes = [r for r in indexes if 0<r<=n]
			except:
				indexes = []
		return indexes
	else:
		sys.stdout.write("Nothing to choose...\n")
		return False


def chooseItem(msg, *elem):
	n = len(elem)
	if n > 1:
		sys.stdout.write(msg + "\n")
		for i in range(n):
			sys.stdout.write("    %d - %s\n" % (i+1, elem[i]))
		i = 0
		while i < 1 or i > n:
			try:
				i = input("Choose an item: [1-%d]> " % n)
				i = int(i)
			except:
				i = 0
		return elem[i-1]
	elif n == 1:
		return elem[0]
	else:
		sys.stdout.write("Nothing to choose...\n")
		return False


def hidenInput(msg):
	data = getpass.getpass(msg)
	if isinstance(data, bytes):
		data = data.decode(sys.stdin.encoding)
	return data


def findAccounts():
	try:
		return [os.path.splitext(name)[0] for name in os.listdir(os.path.join(HOME, ".account", cfg.network)) if name.endswith(".account")]
	except:
		return []


def createBase(secret):
	hx = [e for e in "0123456789abcdef"]
	base = ""
	for c in hexlify(hashlib.md5(secret.encode() if not isinstance(secret, bytes) else secret).digest()):
		try: base += hx.pop(hx.index(c))
		except: pass
	return base + "".join(hx)


def scramble(base, hexa):
	result = bytearray()
	for c in hexa:
		result.append(base.index(c))
	return bytes(result)


def unScramble(base, data):
	result = ""
	for b in data:
		result += base[basint(b)]
	return result


def dumpAccount(base, address, privateKey, secondPrivateKey=None, name="unamed"):
	folder = os.path.join(HOME, ".account", cfg.network)
	if not os.path.exists(folder):
		os.makedirs(folder)
	filename = os.path.join(folder, name+".account")
	data = bytearray()
	with io.open(filename, "wb") as out:
		addr = scramble(base, hexlify(address.encode("utf-8")))
		data.append(len(addr))
		data.extend(addr)

		key1 = scramble(base, privateKey)
		data.append(len(key1))
		data.extend(key1)

		if secondPrivateKey:
			key2 = scramble(base, secondPrivateKey)
			data.append(len(key2))
			data.extend(key2)
		
		out.write(data)


def loadAccount(base, name):
	filepath = os.path.join(HOME, ".account", cfg.network, name+".account")
	result = {}
	if os.path.exists(filepath):
		with io.open(filepath, "rb") as in_:
			data = in_.read()
			try: data = data.encode("utf-8")
			except: pass

			i = 0
			len_addr = basint(data[i])
			i += 1
			result["address"] = unhexlify(unScramble(base, data[i:i+len_addr])).decode("utf-8")
			i += len_addr
			len_key1 =  basint(data[i])
			i += 1
			result["privateKey"] = unScramble(base, data[i:i+len_key1])
			i += len_key1

			if i < len(data):
				len_key2 = basint(data[i])
				i += 1
				result["secondPrivateKey"] = unScramble(base, data[i:i+len_key2])
			
	return result

