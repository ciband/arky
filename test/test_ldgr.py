# -*- coding: utf-8 -*-
import unittest

from arky import ldgr, rest, slots

from six import PY3

if PY3:
	from unittest.mock import patch
else:
	from mock import patch


"""
These tests are running against a mocked dongle. In case you want to run them against a proper
dongle, you need to remove the patch from the tests, for example:

```
with patch.object(ldgr, 'getDongle', return_value=MockedHIDDongleHIDAPI()):
	public_key = ldgr.getPublicKey(dongle_path)
```

becomes:

```
public_key = ldgr.getPublicKey(dongle_path)
```

Possible Exceptions raised in ledgerblue.comm and what they mean:
- Exception : Invalid status 6985 - cancel/reject transaction
- Exception : Invalid status 6700 - raised when Ark not selected in the ledger
- Exception : No dongle found - if dongle not connected OR pin not entered (dongle is locked)
"""


class TestLdgr(unittest.TestCase):

	# derivation path
	path = "44'/1'/0'/0/0"

	def test_getPublicKey(self):
		"""
		Try getting a public key from a ledger wallet
		"""
		dongle_path = ldgr.parseBip32Path(self.path)
		with patch.object(ldgr, 'getDongle', return_value=MockedHIDDongleHIDAPI()):
			public_key = ldgr.getPublicKey(dongle_path)
		assert public_key

	def test_signTx(self):
		"""
		Test signing a transaction directly from a ledger wallet
		"""
		rest.use("dark")

		with patch.object(ldgr, 'getDongle', return_value=MockedHIDDongleHIDAPI()):
			tx = dict(
				vendorField="First Tx using ledger with arky!",
				timestamp=int(slots.getTime()),
				type=0,
				amount=1,
				recipientId='DUGvQBxLzQqrNy68asPcU3stWQyzVq8G49',
				fee=10000000
			)
			signed_tx = ldgr.signTx(tx, self.path)
		assert signed_tx


class MockedHIDDongleHIDAPI():
	"""
	A mocked HIDDongleHIDAPI object that should only be used in a test suite
	"""

	def __init__(self, *args, **kwargs):
		pass

	def exchange(self, apdu, timeout=20000):
		public_key_apdu = (
			b'\xe0\x02\x00@\x15\x05\x80\x00\x00,\x80\x00\x00\x01\x80\x00\x00\x00\x00\x00\x00\x00'
			b'\x00\x00\x00\x00'
		)
		# apdu containing the "First Tx using ledger with arky!" is from a generated transaction
		# abd - we are able to recognize it because of msg in the vendorField
		if b'First Tx using ledger with arky!' in apdu:
			return bytearray(
				b'0E\x02!\x00\xc9\x0cb\x1cFG>8\xc6v\xf5l1\xceb\xa6\x9f\xfa\xfbEf%OC2\x9d\xcc\xff'
				b'\xf7\x0b\xe2\xa8\x02 \x05\x1f5\xd9\xb0\xe2M\x81`\xb3\xfd\xb8\xa9\xfa\xc5;&R3`'
				b'\x15\x1f\xa9J\x9aj\xd9\xdf\x15\xbb~\x8c'
			)
		elif apdu == public_key_apdu:
			return bytearray(
				b'!\x03e\xfa\xde\xd46\x7f*L\xd5\xe9"\xfe\x9b\x10<wl\x90\xbaB2\x97\x1b\xdch\x00\x0cn'
				b'\x05Z\xcd{"AJg8hSruznpX2JWCtsmHb77GjZBTPUNQLi'
			)

	def close(self):
		pass


if __name__ == '__main__':
	unittest.main()
