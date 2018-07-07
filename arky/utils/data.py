# -*- coding: utf-8 -*-
import hashlib
import io
import os
import json

from arky import cfg, HOME, ROOT, exceptions
from arky.utils.bin import basint, hexlify, unhexlify


def findNetworks():
	"""
	Get a list of all available networks
	"""
	path = os.path.join(ROOT, "net")
	if not os.path.exists(path):
		return []
	networks = []
	for name in os.listdir(path):
		if name.endswith(".net"):
			networks.append(os.path.splitext(name)[0])
	return networks


def findAccounts():
	"""
	Get a list of all available account
	"""
	path = os.path.join(HOME, ".account", cfg.network)
	if not os.path.exists(path):
		return []
	accounts = []
	for name in os.listdir(path):
		if name.endswith(".account"):
			accounts.append(os.path.splitext(name)[0])
	return accounts


def createBase(secret):
	"""
	Create a base from a given secret
	"""
	hx = [e for e in "0123456789abcdef"]
	base = ""
	if not isinstance(secret, bytes):
		secret = secret.encode()
	for c in hexlify(hashlib.md5(secret).digest()):
		try:
			base += hx.pop(hx.index(c))
		except:
			pass
	return base + "".join(hx)


def scramble(base, hexa):
	"""
	Scramble given base and hex
	"""
	result = bytearray()
	for c in hexa:
		result.append(base.index(c))
	return bytes(result)


def unScramble(base, data):
	"""
	Unscramble given scrambed data using the provided base
	"""
	result = ""
	for b in data:
		result += base[basint(b)]
	return result


def dumpAccount(base, address, privateKey, secondPrivateKey=None, name="unamed"):
    """
    Store account data into file
    """
    folder = os.path.join(HOME, ".account", cfg.network)
    if not os.path.exists(folder):
        os.makedirs(folder)
    filename = os.path.join(folder, name + ".account")
    data = bytearray()

    if isinstance(address, str):
        address = address.encode()
    addr = scramble(base, hexlify(address))
    data.append(len(addr))
    data.extend(addr)

    key1 = scramble(base, privateKey)
    data.append(len(key1))
    data.extend(key1)

    # Checksum used to verify the data gets unscrabled correctly.
    checksum = hashlib.sha256(address).digest()
    data.append(len(checksum))
    data.extend(checksum)

    if secondPrivateKey:
        key2 = scramble(base, secondPrivateKey)
        data.append(len(key2))
        data.extend(key2)

    with io.open(filename, "wb") as out:
        out.write(data)


def loadAccount(base, name="unamed"):
	"""
	Load account data from file
	"""
	filepath = os.path.join(HOME, ".account", cfg.network, name + ".account")
	result = {}
	if os.path.exists(filepath):
		with io.open(filepath, "rb") as in_:
			data = in_.read()
			try:
				data = data.encode("utf-8")
			except:
				pass

			i = 0
			len_addr = basint(data[i])
			i += 1
			result["address"] = unhexlify(unScramble(base, data[i:i + len_addr]))
			i += len_addr
			len_key1 = basint(data[i])
			i += 1
			result["privateKey"] = unScramble(base, data[i:i + len_key1])
			i += len_key1
			len_checksum = basint(data[i])
			i += 1
			checksum = data[i:i + len_checksum]
			i += len_checksum

			addr_hash = hashlib.sha256(result["address"]).digest()
			if addr_hash != checksum:
				raise exceptions.BadPinError()

			if i < len(data):
				len_key2 = basint(data[i])
				i += 1
				result["secondPrivateKey"] = unScramble(base, data[i:i + len_key2])

	return result


def dumpJson(cnf, name, folder=None):
	filename = os.path.join(folder or HOME, name)
	with io.open(filename, "wb") as outfile:
		outfile.write(json.dumps(cnf, indent=2).encode())
	return os.path.basename(filename)


def loadJson(name, folder=None):
	filename = os.path.join(folder or HOME, name)
	data = {}
	if os.path.exists(filename):
		with io.open(filename, "rb") as file:
			content = file.read()
			data = json.loads(content.decode()) if content else {}
	return data


def popJson(name, folder=None):
	filename = os.path.join(folder or HOME, name)
	if os.path.exists(filename):
		os.remove(filename)
