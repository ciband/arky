# -*- encoding: utf8 -*-
# © Toons

import unittest
import arky.rest
import arky.util

class TestArkCrypto(unittest.TestCase):

	@classmethod
	def setUpClass(self):
		arky.rest.use("dark")
		# here is a valid tx :
		# amount = 100000000
		# secret = "secret"
		# timestamp = devnet begintime
		self.tx = {
			'type': 0,           # send-type transaction
			'fee': 10000000,     # arky.rest.cfg.fees["send"]
			'amount': 100000000, # 1 DARK = 100000000 satoshi
			'timestamp': 736409, # arky.rest.cfg.begintime.toordinal()
			'senderPublicKey': 
				'03a02b9d5fdd1307c2ee4652ba54d492d1fd11a7d1bb3f3a44c4a05e79f19de933',
			'signature':
				'304402205ee5487995b0bbdb8a062c7ad45051b321cc32cd535b404c8b02bfd85fe4f6d80220'
				'2230e40dbaa57e3f7275e0ef65a439a16c406f2f9b0a266d819ef8f0b375aefa',
			'id': 'a299642a90a25fdfea93eab43cf18c6ab21f1c16565d64066f896001594fd892',
		}
		# hexadecimal tx hash 
		self.hexaTx = \
			"00993c0b0003a02b9d5fdd1307c2ee4652ba54d492d1fd11a7d1bb3f3a44c4a05e79f19de9330000"\
			"00000000000000000000000000000000000000000000000000000000000000000000000000000000"\
			"00000000000000000000000000000000000000000000000000000000000000000000000000000000"\
			"00000000e1f505000000008096980000000000304402205ee5487995b0bbdb8a062c7ad45051b321"\
			"cc32cd535b404c8b02bfd85fe4f6d802202230e40dbaa57e3f7275e0ef65a439a16c406f2f9b0a26"\
			"6d819ef8f0b375aefa"

	def test_get_address(self):
		self.assertEqual(
			'D7seWn8JLVwX4nHd9hh2Lf7gvZNiRJ7qLk',
			arky.core.crypto.getAddress(self.tx["senderPublicKey"])
		)

	def test_signature(self):
		keys = arky.core.crypto.getKeys("secret")
		message = "test message".encode("utf-8")
		signature = arky.core.crypto.getSignatureFromBytes(message, keys["privateKey"])
		self.assertEqual(
			True,
			arky.core.crypto.verifySignatureFromBytes(message, keys["publicKey"], signature)
		)

	def test_get_id(self):
		self.assertEqual(
			'a299642a90a25fdfea93eab43cf18c6ab21f1c16565d64066f896001594fd892',
			arky.core.crypto.getId(self.tx)
		)

	def test_get_id_from_bytes(self):
		self.assertEqual(
			'a299642a90a25fdfea93eab43cf18c6ab21f1c16565d64066f896001594fd892',
			arky.core.crypto.getIdFromBytes(arky.util.unhexlify(self.hexaTx))
		)

	def test_bake_transaction(self):
		self.assertEqual(
			self.tx,
			arky.core.crypto.bakeTransaction(
				secret="secret",
				timestamp=arky.rest.cfg.begintime.toordinal(),
				amount=100000000
			)
		)

	def test_get_bytes(self):
		self.assertEqual(
			self.hexaTx,
			arky.util.hexlify(arky.core.crypto.getBytes(self.tx))
		)


class TestLskCrypto(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		arky.rest.use("lisk")

	def test_get_keys(self):
		keys = arky.core.crypto.getKeys("secret")
		self.assertEqual(
			keys["publicKey"],
			"5d036a858ce89f844491762eb89e2bfbd50a4a0a0da658e4b2628b25b117ae09"
		)

	def test_get_address(self):
		keys = arky.core.crypto.getKeys("secret")
		address = arky.core.crypto.getAddress(keys["publicKey"])
		self.assertEqual(address, "18160565574430594874L")


if __name__ == '__main__':
	unittest.main()
