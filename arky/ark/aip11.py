# -*- encoding: utf8 -*-
# © Toons

from .. import slots
from .. import rest
from .. import cfg

from . import __PY3__
from . import crypto
from . import init

import struct


C = 0.0001*100000000
rest.POST.createEndpoint(rest.POST, rest.post, "/peer/transactions/v1")


class Payload:
	
	@staticmethod
	def setArkPerByteFees(value):
		global C
		C = value

	@staticmethod
	def get(typ, **kw):
		return crypto.hexlify(getattr(Payload, "type%d"%typ)(**kw))

	@staticmethod
	def type0(**kw):
		try:
			recipientId = crypto.base58.b58decode_check(kw["recipientId"])
		except:
			raise Exception("no recipientId defined")
		return struct.pack("<QI21s" if __PY3__ else ("<QI"+21*"c"),
			kw.get("amount", 0),
			kw.get("expiration", 0),
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
		return struct.pack("<33s", crypto.unhexlify(secondPublicKey)) if __PY3__ else \
	           struct.pack(33*"c", secondPublicKey)

	@staticmethod
	def type2(**kw):
		username = kw.get("username", False)
		if username:
			length = len(username)
			if 3 <= length <= 255:
				return struct.pack("<B%ds"%length, length, username.encode()) if __PY3__ else \
				       struct.pack("<B" + length*"c", length, username)
			else:
				raise Exception("bad username length [3-255]: %s" % username)
		else:
			raise Exception("no username defined")

	@staticmethod
	def type3(**kw):
		pass


def getHeaders(**kw):
	if "secret" in kw:
		publicKey = crypto.getKeys(kw["secret"])["publicKey"]
	elif "publicKey" in kw:
		publicKey = kw["publicKey"]
	else:
		raise Exception("Can not initialize transaction (no secret or publicKey given)")

	header = struct.pack("<BBBBI",
		kw.get("head", 0xff),
		kw.get("version", 0x02),
		kw.get("network", int(cfg.marker, base=16)),
		kw.get("type", 0),
		int(slots.getTime())
	)

	header += struct.pack("<33s", crypto.unhexlify(publicKey)) if __PY3__ else \
	          struct.pack(33*"c", publicKey)

	header += struct.pack("<Q", kw.get("fees", 0))

	vendorField = kw.get("vendorField", "")
	n = min(255, len(vendorField))
	header += struct.pack("<B", n)
	if n > 0:
		header += struct.pack("<%ss"%n, crypto.unhexlify(publicKey[:n])) if __PY3__ else \
		          struct.pack(n*"c", publicKey[:n])

	return crypto.hexlify(header)


def bakePayload(**kw):
	if "publicKey" in kw and "privateKey" in kw:
		keys = {}
		keys["publicKey"] = kw["publicKey"]
		keys["privateKey"] = kw["privateKey"]
	elif "secret" in kw:
		keys = crypto.getKeys(kw["secret"])
	else:
		raise Exception("Can not initialize transaction (no secret or keys given)")

	payload = Payload.get(kw.get("type", 0), **kw)
	kw["fees"] = int((kw.get("type", 0) + len(payload) + 47) * C)
	header = getHeaders(**kw)
	payload = header + payload

	payload += crypto.getSignatureFromBytes(crypto.unhexlify(payload), keys["privateKey"])
	if kw.get("secondSecret", False):
		secondKeys = crypto.getKeys(kw["secondSecret"])
		payload += crypto.getSignatureFromBytes(crypto.unhexlify(payload), secondKeys["privateKey"])
	elif kw.get("secondPrivateKey", False):
		payload += crypto.getSignatureFromBytes(crypto.unhexlify(payload), kw["secondPrivateKey"])
	# identify payload
	payload += crypto.getIdFromBytes(crypto.unhexlify(payload))

	return payload


# This function is a high-level broadcasting for a single tx
def sendTransaction(**kw):
	tx = bakePayload(**dict([k,v] for k,v in kw.items() if v))
	result = rest.POST.peer.transactions.v1(peer=cfg.peers[0], transactions=[tx])
	success = 1 if result["success"] else 0
	for peer in cfg.peers[1:]:
		if rest.POST.peer.transactions.v1(peer=peer, transactions=[tx])["success"]:
			success += 1
	result["broadcast"] = "%.1f%%" % (100.*success/len(cfg.peers))
	return result

#######################
## basic transaction ##
#######################

# def sendToken(amount, recipientId, vendorField, secret, secondSecret=None):
# 	return sendTransaction(
# 		amount=amount,
# 		recipientId=recipientId,
# 		vendorField=VendorField,
# 		secret=secret,
# 		secondSecret=secondSecret
# 	)

# def registerSecondPublicKey(secondPublicKey, secret, secondSecret=None):
# 	keys = crypto.getKeys(secret)
# 	return sendTransaction(
# 		type=1,
# 		publicKey=keys["publicKey"],
# 		privateKey=keys["privateKey"],
# 		secondSecret=secondSecret,
# 		asset={"signature":{"publicKey":secondPublicKey}}
# 	)

# def registerSecondPassphrase(secondPassphrase, secret, secondSecret=None):
# 	secondKeys = crypto.getKeys(secondPassphrase)
# 	return registerSecondPublicKey(secondKeys["publicKey"], secret, secondSecret)

# def registerDelegate(username, secret, secondSecret=None):
# 	keys = crypto.getKeys(secret)
# 	return sendTransaction(
# 		type=2,
# 		publicKey=keys["publicKey"],
# 		privateKey=keys["privateKey"],
# 		secondSecret=secondSecret,
# 		asset={"delegate":{"username":username, "publicKey":keys["publicKey"]}}
# 	)

# def upVoteDelegate(usernames, secret, secondSecret=None):
# 	keys = crypto.getKeys(secret)
# 	req = rest.GET.api.delegates.get(username=usernames[-1])
# 	if req["success"]:
# 		return sendTransaction(
# 			type=3,
# 			publicKey=keys["publicKey"],
# 			recipientId=crypto.getAddress(keys["publicKey"]),
# 			privateKey=keys["privateKey"],
# 			secondSecret=secondSecret,
# 			asset={"votes":["+%s"%req["delegate"]["publicKey"]]}
# 		)

# def downVoteDelegate(usernames, secret, secondSecret=None):
# 	keys = crypto.getKeys(secret)
# 	req = rest.GET.api.delegates.get(username=usernames[-1])
# 	if req["success"]:
# 		return sendTransaction(
# 			type=3,
# 			publicKey=keys["publicKey"],
# 			recipientId=crypto.getAddress(keys["publicKey"]),
# 			privateKey=keys["privateKey"],
# 			secondSecret=secondSecret,
# 			asset={"votes":["-%s"%req["delegate"]["publicKey"]]}
# 		)
