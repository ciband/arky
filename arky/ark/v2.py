# -*- coding: utf-8 -*-
# © Toons

from collections import OrderedDict
import struct

from six import PY3

from .. import slots
from .. import rest
from .. import cfg

from . import crypto

PKFMT = "%ss"%33 if PY3 else 33*"c"


class Payload(object):

	C = 0.0001 * 100000000

	@staticmethod
	def setArkPerByteFees(value):
		Payload.C = value

	@staticmethod
	def get(typ, **kw):
		"""
		Return a payload from keyword parameters.
		"""
		return crypto.hexlify(getattr(Payload, "type%d" % typ)(**kw))

	@staticmethod
	def type0(**kw):
		try:
			recipientId = crypto.base58.b58decode_check(kw["recipientId"])
		except:
			raise Exception("no recipientId defined")
		return struct.pack(
			"<QI21s" if PY3 else ("<QI" + 21 * "c"),
			int(kw.get("amount", 0)),
			int(kw.get("expiration", 0)),
			recipientId
		)

	@staticmethod
	def type1(**kw):
		if "secondSecret" in kw:
			secondPublicKey = crypto.getKeys(kw["secondSecret"])["publicKey"]
		elif "secondPublicKey" in kw:
			secondPublicKey = kw["secondPublicKey"]
		else:
			raise Exception("no secondSecret or secondPublicKey given")
		return struct.pack("<33s", crypto.unhexlify(secondPublicKey)) if PY3 else \
			   struct.pack(33 * "c", secondPublicKey)

	@staticmethod
	def type2(**kw):
		username = kw.get("username", False)
		if username:
			length = len(username)
			if 3 <= length <= 255:
				return struct.pack("<B%ds" % length, length, username.encode()) if PY3 else \
					   struct.pack("<B" + length * "c", length, username)
			else:
				raise Exception("bad username length [3-255]: %s" % username)
		else:
			raise Exception("no username defined")

	@staticmethod
	def type3(**kw):
		delegatePublicKey = kw.get("delegatePublicKey", False)
		if delegatePublicKey:
			length = len(delegatePublicKey)
			return struct.pack("<%ds" % length, delegatePublicKey.encode()) if PY3 else \
				   struct.pack("<" + length*"c", delegatePublicKey)
		else:
			raise Exception("no up/down vote given")



class Transaction:

	header = {
		"head": (0, "<B"),
		"version": (2*struct.calcsize("<B"), "<B"),
		"network": (2*struct.calcsize("<BB"), "<B"),
		"type": (2*struct.calcsize("<BBB"), "<B"),
		"timestamp": (2*struct.calcsize("<BBBB"), "<I"),
		"publicKey": (2*struct.calcsize("<BBBBI"), "<"+PKFMT),
		"senderPublicKey": (2*struct.calcsize("<BBBBI"), "<"+PKFMT),
		"fees": (2*struct.calcsize("<BBBBI"+PKFMT), "<Q"),
		"lenVF": (2*struct.calcsize("<BBBBI"+PKFMT+"Q"), "<B")
	}

	def __init__(self, *args, **kwargs):
		self.__data = crypto.hexlify(struct.pack(
			"<BBBBI",
			kwargs.get("head", 0xff),
			kwargs.get("version", 0x02),
			kwargs.get("network", int(cfg.marker, base=16)),
			kwargs.get("type", 0),
			int(kwargs.get("timestamp", slots.getTime()))
		))
		self.__payload_start = None
		self.__signature_start = None
		for key in ["vendorField", "publicKey", "senderPublicKey"]:
			self[key] = kwargs.get(key, "")

	def __setitem__(self, item, value):
		if isinstance(item, slice):
			lst = list(self.__data)
			lst[item.start:item.stop] = list(value)
			self.__data = "".join(lst)
		elif item == "vendorField":
			n = len(value)
			start, fmt = Transaction.header["lenVF"]
			start = start + 2*struct.calcsize(fmt)
			value = value.encode("utf-8") if not isinstance(value, bytes) else value
			old_n = self["lenVF"]
			self["lenVF"] = n
			self[start:start+ 2*old_n] = crypto.hexlify(value)
			self.__payload_start = len(self.__data)
		else:
			try:
				if isinstance(value, str):
					value = crypto.unhexlify(value)
				start, fmt = Transaction.header[item]
				end = start + 2*struct.calcsize(fmt)
				if len(self.__data) < end:
					self.__data += (end-len(self.__data))*"0"
				data = crypto.hexlify(struct.pack(fmt, *(value,)))
				self[start:end] = data
			except KeyError:
				raise KeyError("Transaction have no item %s" % item)
			else:
				self._reset()

	def __getitem__(self, item):
		if isinstance(item, slice):
			lst = list(self.__data)
			return "".join(lst[item.start:item.stop:1 if not item.step else item.step])
		elif item == "vendorField":
			start, fmt = Transaction.header["lenVF"]
			start = start+2*struct.calcsize(fmt)
			return crypto.unhexlify(self[start:start+2*self["lenVF"]]).decode("utf-8")
		elif item == "id":
			if self.identified:
				return self[-32*2:]
			else:
				raise KeyError("Transactionis not identified yet")
		else:
			try:
				start, fmt = Transaction.header[item]
				end = start + 2*struct.calcsize(fmt)
				if len(self.__data) < end:
					self.__data += (end-len(self.__data))*"0"
				result = struct.unpack(fmt, crypto.unhexlify(self[start:end]))
				if len(result):
					data = result[0]
					return crypto.hexlify(data) if isinstance(data, bytes) else data
				else:
					raise Exception("Can not unpack value")
			except KeyError:
				raise KeyError("Transaction have no item %s" % item)

	def __repr__(self):
		return "%r" % self.__data

	def _reset(self):
		if self.__payload_start:
			if self.__signature_start:
				self.__data = self.__data[:self.__signature_start]
				self.__signature_start = len(self.__data)
				self.finalized = True
			else:
				self.__data = self.__data[:self.__payload_start]
				self.__signature_start = None
				self.finalized = False
		else:
			self.__payload_start = len(self.__data)
		self.identified = False
		self.signSigned = False
		self.signed = False

	def finalize(self, **kwargs):
		payload = Payload.get(self["type"], **kwargs)
		amount = kwargs.get("amount", 0)
		fees = int((self["type"] + (len(self.__data)+len(payload))/2) * Payload.C)
		if amount >= fees and kwargs.get("fees_included", False):
			kwargs["amount"] = amount - fees
			payload = Payload.get(self["type"], **kwargs)
		self["fees"] = fees
		self.__payload_start = len(self.__data)
		self.__data += payload
		self.finalized = True

	def sign(self, **kwargs):
		if self.finalized and not self.signed:
			self.__signature_start = len(self.__data)
			if "privateKey" in kwargs:
				keys = {}
				keys["privateKey"] = kwargs["privateKey"]
			elif "secret" in kwargs:
				keys = crypto.getKeys(kwargs["secret"])
				self["publicKey"] = keys["publicKey"]
			else:
				raise Exception("Can not sign transaction (no secret or keys given)")
			self.__data += crypto.getSignatureFromBytes(crypto.unhexlify(self.__data), keys["privateKey"])
			self.signed = True
		if self.finalized and not self.signSigned:
			if kwargs.get("secondSecret", False):
				secondKeys = crypto.getKeys(kwargs["secondSecret"])
				self.__data += crypto.getSignatureFromBytes(crypto.unhexlify(self.__data), secondKeys["privateKey"])
				self.signSigned = True
			elif kwargs.get("secondPrivateKey", False):
				self.__data += crypto.getSignatureFromBytes(crypto.unhexlify(self.__data), kwargs["secondPrivateKey"])
				self.signSigned = True

	def identify(self):
		if not self.identified:
			self.__data += crypto.getIdFromBytes(crypto.unhexlify(self.__data))
			self.identified = True

	def serialize(self):
		keys = list(Transaction.header.keys()) + ["vendorField", "senderPublicKey"]
		return OrderedDict(
			header=OrderedDict([key,self[key]] for key in keys),
			payload=self.__data[self.__payload_start:self.__signature_start],
			signatures=self.__data[self.__signature_start:-32*2],
			id=self.__data[-32*2:]
		)


def sendPayload(*payloads):
	success, msgs, ids = 0, set(), set()

	for peer in cfg.peers:
		response = rest.POST.v2.peer.transactions(peer=peer, transactions=["%r"%p for p in payloads])
		success += 1 if response["success"] else 0

		if "message" in response:
			msgs.update([response["message"]])

		if "transactionIds" in response:
			ids.update(response["transactionIds"])

	return {
		"success": "%.1f%%" % (float(100) * success / len(cfg.peers)),
		"transactions": list(ids),
		"messages": list(msgs)
	}


def bakeTransaction(**kw):
	kw = dict([k, v] for k, v in kw.items() if v)
	tx = Transaction(**kw)
	tx.finalize(**kw)
	tx.sign(**kw)
	tx.identify()
	return tx


####################################################
# high-level broadcasting function for a single tx #
####################################################
def sendTransaction(**kw):
	tx = bakeTransaction(**dict([k, v] for k, v in kw.items() if v))
	sendPayload(tx)


#######################
#  basic transaction  #
#######################

def sendToken(amount, recipientId, secret, secondSecret=None, vendorField=None):
	return sendTransaction(
		amount=amount,
		recipientId=recipientId,
		vendorField=VendorField,
		secret=secret,
		secondSecret=secondSecret
	)


def registerSecondPublicKey(secondPublicKey, secret):
	keys = crypto.getKeys(secret)
	return sendTransaction(
		type=1,
		publicKey=keys["publicKey"],
		privateKey=keys["privateKey"],
		secondPublicKey=secondPublicKey
	)


def registerSecondPassphrase(secret, secondSecret):
	secondKeys = crypto.getKeys(secondSecret)
	return registerSecondPublicKey(secondKeys["publicKey"], secret)


def registerDelegate(username, secret, secondSecret=None):
	keys = crypto.getKeys(secret)
	return sendTransaction(
		type=2,
		publicKey=keys["publicKey"],
		privateKey=keys["privateKey"],
		secondSecret=secondSecret,
		username = username
	)


def upVoteDelegate(usernames, secret, secondSecret=None):
	keys = crypto.getKeys(secret)
	req = rest.GET.api.delegates.get(username=usernames[-1])
	if req["success"]:
		return sendTransaction(
			type=3,
			publicKey=keys["publicKey"],
			recipientId=crypto.getAddress(keys["publicKey"]),
			privateKey=keys["privateKey"],
			secondSecret=secondSecret,
			delegatePublicKey="01"+req["delegate"]["publicKey"]
		)

def downVoteDelegate(usernames, secret, secondSecret=None):
	keys = crypto.getKeys(secret)
	req = rest.GET.api.delegates.get(username=usernames[-1])
	if req["success"]:
		return sendTransaction(
			type=3,
			publicKey=keys["publicKey"],
			recipientId=crypto.getAddress(keys["publicKey"]),
			privateKey=keys["privateKey"],
			secondSecret=secondSecret,
			delegatePublicKey="00"+req["delegate"]["publicKey"]
		)
