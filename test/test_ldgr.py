# -*- encoding: utf8 -*-
# © Toons
import os
import sys

from ledgerblue.comm import getDongle
import arky

from arky import rest
from arky import ldgr
from arky import util
from arky import slots

if os.environ['ENV'] == 'ci':
    pass
else:
    rest.use("ark")

    dpath = "44'/111'/0'/0/0"
    print("Recovering publicKey and Addresses from derivation path : <%s>..." % dpath)
    apdu = ldgr.buildPkeyApdu(ldgr.parseBip32Path(dpath))
    dongle = getDongle()
    data = bytes(dongle.exchange(apdu))
    dongle.close()

    len_pkey = util.basint(data[0])
    pkey = util.hexlify(data[1:len_pkey+1])
    print(pkey)
    len_address = util.basint(data[len_pkey+1])
    print(data[-len_address:].decode())

    #put your recipient address here
    recipientId = "..."

    tx = dict(
        senderPublicKey=pkey,
        vendorField="First Tx using ledger with arky !",
        timestamp=int(slots.getTime()),
        type=0,
        amount=1,
        recipientId=recipientId,
        fee=10000000
    )

    ldgr.signTx(tx, dpath, True)

    print(tx)

    print(arky.core.sendPayload(tx))
