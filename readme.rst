.. image:: https://github.com/Moustikitos/arky/raw/master/arky-logo.png
   :target: https://ark.io

Copyright 2016-2018 **Toons**, Copyright 2018 **ARK**, `MIT licence`_

.. image:: https://travis-ci.org/ArkEcosystem/arky.svg?branch=aip11
    :target: https://travis-ci.org/ArkEcosystem/arky

Install
=======

Ubuntu / OSX
^^^^^^^^^^^^

From development version

``sudo -H pip install https://github.com/ArkEcosystem/arky/archive/aip11.zip``

If you work with ``python3``

``sudo -H pip3 install https://github.com/ArkEcosystem/arky/archive/aip11.zip``

Windows 
^^^^^^^

From development version

``pip install https://github.com/ArkEcosystem/arky/archive/aip11-dev.zip``

REST API
========

``rest`` module allows developpers to send requests to the blockchain.

>>> import arky.rest
>>> arky.rest.use("ark")

It loads the ``ark.net`` file and create associated REST API endpoints.
All endpoints can be reached using this syntax :

``arky.rest.[METHOD].[endpoints with "/" replaced by "."](param=value, ...[returnKey=name])``

>>> # http equivalent [PEER ADDRESS]/api/delegates/get?username=arky
>>> arky.rest.GET.api.delegates.get(username="arky")
{'delegate': {'productivity': 99.22, 'producedblocks': 42283, 'approval': 1.06, 
'rate': 19, 'publicKey': '030da05984d579395ce276c0dd6ca0a60140a3c3d964423a04e7ab
e110d60a15e9', 'username': 'arky', 'vote': '137484978342696', 'address': 'ARfDVW
Z7Zwkox3ZXtMQQY1HYSANMB88vWE', 'missedblocks': 334}, 'success': True}

It returns a python dictionary transposed from server json response. You can
provide a ``returnKey`` option value to get the field you want from server response :

>>> arky.rest.use("oxy")
>>> arky.rest.GET.api.delegates.get(username="toons", returnKey="delegate")
{'rate': 20, 'producedblocks': 1354, 'approval': 14.36, 'username': 'toons', 'ra
nk': 20, 'publicKey': 'c0f4e7fb7555fd19de2b6a9de92f02b44cef56c782ca0f6983607b7f4
e508ef9', 'productivity': 99.63, 'missedblocks': 5, 'vote': '1476176009882003', 
'address': '15981732227677853647X'}

Blockchain ``core``
===================

``arky.rest.use`` loads a blockchain package find in  ``*.net`` file as ``arky.core``.
Blockchain package define the current interface :

* ``arky.core.crypto.getKeys(secret)``
* ``arky.core.crypto.getAddress(publicKey)``
* ``arky.core.crypto.getSignature(tx, privateKey)``
* ``arky.core.crypto.getId(tx)``
* ``arky.core.crypto.getBytes(tx)``
* ``arky.core.crypto.bakeTransaction(**kw)``
* ``arky.core.sendTransaction(**kw)``
* ``arky.core.sendPayload(*payloads)``
* ``arky.core.sendToken(amount, recipientId, secret, secondSecret=None, vendorField=None)``
* ``arky.core.registerSecondPublicKey(secondPublicKey, secret, secondSecret=None)``
* ``arky.core.registerSecondPassphrase(secondPassphrase, secret, secondSecret=None)``
* ``arky.core.registerDelegate(username, secret, secondSecret=None)``
* ``arky.core.upVoteDelegate(usernames, secret, secondSecret=None)``
* ``arky.core.downVoteDelegate(usernames, secret, secondSecret=None)``

``arky.core`` create transaction localy using ``pynacl`` and ``ecdsa`` crypto libraries
so no secret is sent trough the network.

Send coins
^^^^^^^^^^

Amount are given in SATOSHI.

>>> arky.rest.use("toxy")
>>> arky.core.sendToken(amount=100000000, recipientId="15981732227677853647X",
...                     secret="secret", secondSecret="secondSecret")
{'id': '13372419325129159475', 'success': True}

>>> arky.rest.use("dark")
>>> arky.core.sendToken(amount=100000000, recipientId="15981732227677853647X",
...                     secret="secret", secondSecret="secondSecret",
...                     vendorField="Your smart bridge message here")
{'success': True, 'transactionIds': ['24584ec149106e6206445106af8176cc885edf12ae
0c4534d2e4a3b4214d4a3f'], 'broadcast': '90.0%'}

Vote for delegate
^^^^^^^^^^^^^^^^^

>>> arky.rest.use("toxy")
>>> arky.core.upVoteDelegate(["toons", "unused"],
...                          secret="secret", secondSecret="secondSecret")
{'id': '10107701353010554951', 'success': True}

>>> arky.rest.use("dark")
>>> arky.core.downVoteDelegate(["d_arky"],
...                            secret="secret", secondSecret="secondSecret")
{'broadcast': '100.0%', 'transactionIds': ['ecd663ea46472cd7d72431eb13e9b23ef9c2
6aae8a1004621b871677960d01f1'], 'success': True}

CLI
===

You can use ``arky`` package without writing a line of code trough command
line interface. There are two ways to launch the CLI.

>>> from arky import cli
>>> cli.start()

::

  Welcome to arky-cli [Python x.y.z / arky 1.x]
  Available commands: network, account, delegate, ledger
  cold@.../>

Use network
^^^^^^^^^^^

::

  cold@.../> network use
  Network(s) found:
      1 - ark-aip11
      2 - ark
      3 - dark
      4 - kapu
      5 - lisk
      6 - oxy
      7 - shift
      8 - toxy
      9 - tshift
  Choose an item: [1-9]> 8
  hot@toxy/network>

Link account
^^^^^^^^^^^^

::

  hot@toxy/network> account link secret
  hot@toxy/account[18160...4874X]> send 1.23 12427608128403844156X
  Send 1.23000000 oxycoin to 12427608128403844156X ? [y-n]> y
  Enter second passphrase> secondSecret
      Broadcasting transaction...
           id: 776848717338323058
      success: True

::

  hot@toxy/account[18160...4874X]> status
           secondSignature: 1
           multisignatures: []
           secondPublicKey: 8b509500d5950122b3e446189b4312805515c8e7814a409e09ac5c21935564af
         u_multisignatures: []
        unconfirmedBalance: 2637000000
                 publicKey: 5d036a858ce89f844491762eb89e2bfbd50a4a0a0da658e4b2628b25b117ae09
      unconfirmedSignature: 1
                   address: 18160565574430594874X
                   balance: 2637000000
  hot@toxy/account[18160...4874X]>

Use Ledger Nano S
^^^^^^^^^^^^^^^^^

::

  hot@ark/network> ledger link
  hot@ark/ledger[AerGA...VbMft]> send 1 AUahWfkfr5J4tYakugRbfow7RWVTK35GPW "send 1 ARK from ledger using arky CLI"
  Use ledger key to confirm or or cancel :
      Send 1.00000000 ARK to AUahWfkfr5J4tYakugRbfow7RWVTK35GPW ?
      Broadcasting transaction...
           broadcast: 100.0%
      transactionIds: ['34d4ce9dea2dd4f52e8d6af1977d5f00488694ecbdaf7c45f70a7c46c078c744']
             success: True
  hot@ark/ledger[AerGA...VbMft]>

Author
======

Toons <moustikitos@gmail.com>

Support this project
====================

.. image:: https://github.com/ArkEcosystem/arky/raw/master/ark-logo.png
   :height: 30

Toons Ark address: ``AUahWfkfr5J4tYakugRbfow7RWVTK35GPW``

.. image:: http://bruno.thoorens.free.fr/img/bitcoin.png
   :width: 100

Toons Bitcoin address: ``1qjHtN5SuzvcA8RZSxNPuf79iyLaVjxfc``

**Show gratitude on Gratipay:**

.. image:: http://img.shields.io/gratipay/user/b_py.svg?style=flat-square
   :target: https://gratipay.com/~b_py

**Vote for Toons' delegate arky**

.. _MIT licence: http://htmlpreview.github.com/?https://github.com/Moustikitos/arky/blob/master/arky.html
