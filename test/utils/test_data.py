# -*- coding: utf-8 -*-
import os
import arky
import unittest

from arky.exceptions import BadPinError
from arky.rest import use
from arky.utils.bin import hexlify
from arky.utils.data import (
	dumpJson, dumpAccount, loadAccount, loadJson, popJson, createBase, scramble, unScramble,
	findNetworks, findAccounts
)


class TestUtilsData(unittest.TestCase):

	def test_json(self):
		"""
		When calling `dumpJson` a file with a json dump should be created and we should be able to
		get its contents with `loadJson`. Our `popJson` fn should remove the file.
		"""
		data = {"testing": True}
		filename = "test.txt"
		dumpJson(data, filename)
		data = loadJson(filename)
		assert data["testing"] is True

		# test if file will be removed
		popJson(filename)
		assert not os.path.exists(filename)

	def test_createBase(self):
		pins = [str('abc123'), b'abc123', u'abc123']
		for pin in pins:
			output = createBase(pin)
			assert output == 'e9a18c42b3d5f607'

	def test_scramble_and_unscramble(self):
		# set test data
		pin = "abc123"
		address = "DUGvQBxLzQqrNy68asPcU3stWQyzVq8G49".encode()
		scrambled_result = (
			b"\x06\x06\x0b\x0b\x06\x0f\x0f\r\x0b\x03\x06\x07\x0f\x04\x06\x05\x0f\x02\x0b\x03\x0f"
			b"\x03\x0f\x07\x06\x00\x0f\x01\t\r\t\x04\r\x03\x0f\t\x0b\x0e\r\t\x0b\x0b\t\t\x0f\t"
			b"\x0f\x06\x0b\x0f\x0b\x03\x0f\x01\x0f\x02\x0b\r\x0f\x03\t\x04\x06\x0f\t\x06\t\x01"
		)

		# run test
		base = createBase(pin)
		hexa = hexlify(address)
		scrambled = scramble(base, hexa)
		assert scrambled == scrambled_result

		unscrambled = unScramble(base, scrambled)
		assert hexa == unscrambled

	def test_dumpAccount_findAccounts_loadAccount(self):
		use("dark")

		pin = "abc123"
		address = "DUGvQBxLzQqrNy68asPcU3stWQyzVq8G49".encode()
		privateKey = "123123123"
		base = createBase(pin)

		orig_accounts = findAccounts()
		orig_accounts.append("unamed")

		dumpAccount(base, address, privateKey)

		accounts = findAccounts()
		assert set(accounts) == set(orig_accounts)

		output = loadAccount(base)
		assert output["address"] == address
		assert output["privateKey"] == privateKey

	def test_loadAccount_badPin(self):
		use("dark")

		pin = "abc123"
		address = "DUGvQBxLzQqrNy68asPcU3stWQyzVq8G49".encode()
		privateKey = "123123123"
		base = createBase(pin)

		dumpAccount(base, address, privateKey)

		badPin = "xyz123"
		badBase = createBase(badPin)

		with self.assertRaises(BadPinError) as context:
			loadAccount(badBase)

	def test_findNetworks(self):
		networks = findNetworks()
		assert len(networks) == len(os.listdir(os.path.join(arky.__path__[0], "net")))


if __name__ == '__main__':
	unittest.main()
