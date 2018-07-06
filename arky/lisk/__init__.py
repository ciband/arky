# -*- coding: utf-8 -*-
# © Toons
import sys

from arky import cfg, rest, slots
from arky.lisk import crypto
from arky.utils.http import getDelegatesPublicKeys
from arky.utils.decorators import setInterval


def select_peers():
	selection = []
	for seed in cfg.seeds:
		if rest.check_latency(seed):
			selection.append(seed)

	if len(selection):
		cfg.peers = selection


@setInterval(30)
def rotate_peers():
	select_peers()


def init():
	global DAEMON_PEERS
	resp = rest.GET.api.blocks.getNethash()
	if resp["success"]:
		cfg.headers["version"] = str(rest.GET.api.peers.version(returnKey="version"))
		cfg.headers["nethash"] = resp["nethash"]
		cfg.fees = rest.GET.api.blocks.getFees()["fees"]

		# select peers immediately and keep refreshing them in a thread so we
		# are sure we make requests to working peers
		select_peers()
		DAEMON_PEERS = rotate_peers()
	else:
		sys.stdout.write(
			("%s\n" % resp.get("error", "...")).encode("ascii", errors="replace").decode()
		)
		raise Exception("Initialization error with peer %s" % resp.get("peer", "???"))


def bakeTransaction(**kw):
	if "publicKey" in kw and "privateKey" in kw:
		publicKey, privateKey = kw["publicKey"], kw["privateKey"]
	elif "secret" in kw:
		keys = crypto.getKeys(kw["secret"])
		publicKey = keys["publicKey"]
		privateKey = keys["privateKey"]
	else:
		raise Exception("Can not initialize transaction (no secret or keys given)")

	# put mandatory data
	payload = {
		"timestamp": int(slots.getTime()),
		"type": int(kw.get("type", 0)),
		"amount": int(kw.get("amount", 0)),
		"fee": cfg.fees.get({
			0: "send",
			1: "secondsignature",
			2: "delegate",
			3: "vote",
			# 4: "multisignature",
			# 5: "dapp"
		}[kw.get("type", 0)])
	}
	payload["senderPublicKey"] = publicKey

	# add optional data
	for key in (k for k in ["requesterPublicKey", "recipientId", "asset"] if k in kw):
		payload[key] = kw[key]

	# sign payload
	payload["signature"] = crypto.getSignature(payload, privateKey)
	if kw.get("secondSecret", None):
		secondKeys = crypto.getKeys(kw["secondSecret"])
		payload["signSignature"] = crypto.getSignature(payload, secondKeys["privateKey"])
	elif kw.get("secondPrivateKey", None):
		payload["signSignature"] = crypto.getSignature(payload, kw["secondPrivateKey"])

	# identify payload
	payload["id"] = crypto.getId(payload)

	return payload


def sendPayload(*payloads):
	result = rest.POST.peer.transactions(transactions=payloads)
	if result["success"]:
		result["id"] = [tx["id"] for tx in payloads]
	return result


####################################################
# high-level broadcasting function for a single tx #
####################################################
def sendTransaction(**kw):
	tx = crypto.bakeTransaction(**dict([k, v] for k, v in kw.items() if v))
	result = rest.POST.peer.transactions(transactions=[tx])
	if result["success"]:
		result["id"] = tx["id"]
	return result


#######################
#  basic transaction  #
#######################

def sendToken(amount, recipientId, secret, secondSecret=None):
	return sendTransaction(
		amount=amount,
		recipientId=recipientId,
		secret=secret,
		secondSecret=secondSecret
	)


def registerSecondPublicKey(secondPublicKey, secret):
	keys = crypto.getKeys(secret)
	return sendTransaction(
		type=1,
		publicKey=keys["publicKey"],
		privateKey=keys["privateKey"],
		asset={"signature": {"publicKey": secondPublicKey}}
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
		asset={"delegate": {"username": username, "publicKey": publicKey}}
	)


def upVoteDelegate(usernames, secret, secondSecret=None):
	keys = crypto.getKeys(secret)
	return sendTransaction(
		type=3,
		publicKey=keys["publicKey"],
		privateKey=keys["privateKey"],
		recipientId=crypto.getAddress(keys["publicKey"]),
		secondSecret=secondSecret,
		asset={"votes": ["+%s" % pk for pk in getDelegatesPublicKeys(*usernames)]}
	)


def downVoteDelegate(usernames, secret, secondSecret=None):
	keys = crypto.getKeys(secret)
	return sendTransaction(
		type=3,
		publicKey=keys["publicKey"],
		privateKey=keys["privateKey"],
		recipientId=crypto.getAddress(keys["publicKey"]),
		secondSecret=secondSecret,
		asset={"votes": ["-%s" % pk for pk in getDelegatesPublicKeys(*usernames)]}
	)

