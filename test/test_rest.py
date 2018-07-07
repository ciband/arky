# -*- coding: utf-8 -*-
import unittest

import arky
from arky import ark
from arky import lisk

import requests
import responses


class TestRest(unittest.TestCase):

	def test_use_ark(self):
		"""
		Test if initiating ark does set cfg and core modules
		"""
		arky.rest.use('ark')
		assert ark == arky.core
		assert arky.cfg.network == 'ark'
		assert arky.cfg.familly == 'ark'
		assert len(arky.cfg.peers)

	def test_use_lisk(self):
		"""
		Test if initiating lisk does set cfg and core modules
		"""
		arky.rest.use('lisk')
		assert lisk == arky.core
		assert arky.cfg.network == 'lisk'
		assert arky.cfg.familly == 'lisk'
		assert len(arky.cfg.peers)

	def test_use_invalid_blockchain(self):
		"""
		Test if error is raised
		"""
		with self.assertRaises(Exception) as context:
			arky.rest.use('not-a-blockchain')
		assert str(context.exception) == 'File not found for not-a-blockchain'

if __name__ == '__main__':
	unittest.main()
