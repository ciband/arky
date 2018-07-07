# -*- coding: utf-8 -*-
# © Toons
import logging

from arky import cfg, rest, slots
from arky.utils.decorators import setInterval
from arky.ark import crypto

log = logging.getLogger(__name__)
DAEMON_PEERS = None


def select_peers():
    version = rest.GET.api.peers.version(returnKey='version') or '0.0.0'
    height = rest.GET.api.blocks.getHeight(returnKey='height') or 0
    if isinstance(height, dict) or isinstance(version, dict):
        return

    peers = rest.GET.peer.list().get('peers', [])
    good_peers = []
    for peer in peers:
        if (
            peer.get("delay", 6000) <= cfg.timeout * 1000 and peer.get("version") == version and
            peer.get("height", -1) > height - 10
        ):
            good_peers.append(peer)

    good_peers = sorted(good_peers, key=lambda e: e["delay"])

    min_selection = getattr(cfg, "broadcast", 0)
    selection = []
    for peer in good_peers:
        peer = "http://{ip}:{port}".format(**peer)
        if rest.check_latency(peer):
            selection.append(peer)

        if len(selection) >= min_selection:
            break

    if len(selection) < min_selection:
        log.debug(
            'Broadcast is set to "%s", but managed to get %s peers out of %s.',
            min_selection, len(selection), len(peers)
        )

    if len(selection) >= min_selection:
        cfg.peers = selection
    # else:
    # 	raise Exception('Was not able to get even one live peer out of %s peers.\n' % len(peers))


@setInterval(30)
def rotate_peers():
    select_peers()


def init():
    global DAEMON_PEERS
    response = rest.GET.api.loader.autoconfigure()
    if response["success"]:
        network = response["network"]
        cfg.headers["version"] = str(network.pop('version'))
        cfg.headers["nethash"] = network.pop('nethash')
        cfg.__dict__.update(network)
        cfg.fees = rest.GET.api.blocks.getFees()["fees"]

        # select peers immediately and keep refreshing them in a thread so we
        # are sure we make requests to working peers
        select_peers()
        DAEMON_PEERS = rotate_peers()
    else:
        log.error(response.get('error', '...'))
        raise Exception("Initialization error with peer %s" % response.get("peer", "???"))


def sendPayload(*payloads):
    success, msgs, ids = 0, set(), set()

    for peer in cfg.peers:
        response = rest.POST.peer.transactions(peer=peer, transactions=payloads)
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
    """
    Create transaction localy.

    Argument:
    tx (dict) -- transaction object

    Return dict
    """
    kw = dict([k,v] for k,v in kw.items() if v)

    if "publicKey" in kw and "privateKey" in kw:
        keys = {}
        keys["publicKey"] = kw["publicKey"]
        keys["privateKey"] = kw["privateKey"]
    elif "secret" in kw:
        keys = crypto.getKeys(kw["secret"])
    else:
        keys = {}
        # raise Exception("Can not initialize transaction (no secret or keys given)")

    # put mandatory data
    payload = {
        "timestamp": kw.get("timestamp", int(slots.getTime())),
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

    # add optional data
    for key in ["requesterPublicKey", "recipientId", "vendorField", "asset", "signature", "signSignature", "id"]:
        if key in kw:
            payload[key] = kw[key]

    # add sender public key if any key or secret is given
    if len(keys):
        payload["senderPublicKey"] = keys.get("publicKey", None)

    # sign payload if possible
    # if len(keys):
        payload["signature"] = crypto.getSignature(payload, keys["privateKey"])
        if kw.get("secondSecret", False):
            secondKeys = crypto.getKeys(kw["secondSecret"])
            payload["signSignature"] = crypto.getSignature(payload, secondKeys["privateKey"])
        elif kw.get("secondPrivateKey", False):
            payload["signSignature"] = crypto.getSignature(payload, kw["secondPrivateKey"])
        # identify payload
        payload["id"] = crypto.getId(payload)

    return payload

####################################################
# high-level broadcasting function for a single tx #
####################################################
def sendTransaction(**kwargs):
    tx = crypto.bakeTransaction(**dict([k, v] for k, v in kwargs.items() if v))
    return sendPayload(tx)


########################
#  basic transactions  #
########################

def sendToken(amount, recipientId, secret, secondSecret=None, vendorField=None):
    return sendTransaction(
        amount=amount,
        recipientId=recipientId,
        vendorField=vendorField,
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
        asset={
            "delegate": {
                "username": username, "publicKey": keys["publicKey"]
            }
        }
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
            asset={"votes": ["+%s" % req["delegate"]["publicKey"]]}
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
            asset={"votes": ["-%s" % req["delegate"]["publicKey"]]}
        )

