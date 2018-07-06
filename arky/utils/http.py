# -*- coding: utf-8 -*-
# © Toons

from datetime import datetime, timedelta

import pytz
import requests

from arky import cfg, rest, slots

def getTokenPrice(token, fiat="usd"):
	cmc_ark = requests.get(
		"https://api.coinmarketcap.com/v1/ticker/{0}/?convert={1}".format(token, fiat.upper()),
		verify=cfg.verify
	).json()
	try:
		return float(cmc_ark[0]["price_%s" % fiat.lower()])
	except:
		return 0.


def getCandidates():
	candidates = []
	req = rest.GET.api.delegates(offset=len(candidates), limit=cfg.delegate).get("delegates", [])
	while not len(req) < cfg.delegate:
		candidates.extend(req)
		req = rest.GET.api.delegates(
			offset=len(candidates), limit=cfg.delegate
		).get("delegates", [])
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
	return sorted([t for t in txs if t["timestamp"] >= timestamp], key=lambda e: e["timestamp"], reverse=True)


def getHistory(address, timestamp=0):
	return getTransactions(timestamp, recipientId=address, senderId=address)


def getVoteForce(address, **kw):
	# determine timestamp
	balance = kw.pop("balance", 0) / 100000000.
	if not balance:
		balance = float(rest.GET.api.accounts.getBalance(address=address, returnKey="balance")) / 100000000.
	delta = timedelta(**kw)
	if delta.total_seconds() < 86400:
		return balance
	now = datetime.now(pytz.UTC)
	timestamp_limit = slots.getTime(now - delta)
	# get transaction history
	history = getHistory(address, timestamp_limit)
	# if no transaction over periode integrate balance over delay and return it
	if not history:
		return balance * delta.total_seconds() / 3600
	# else
	end = slots.getTime(now)
	sum_ = 0.
	brk = False
	for tx in history:
		delta_t = (end - tx["timestamp"]) / 3600
		sum_ += balance * delta_t
		balance += ((tx["fee"] + tx["amount"]) if tx["senderId"] == address else -tx["amount"]) / 100000000.
		if tx["type"] == 3:
			brk = True
			break
		end = tx["timestamp"]
	if not brk:
		sum_ += balance * (end - timestamp_limit) / 3600
	return sum_
