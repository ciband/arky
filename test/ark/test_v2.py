# -*- coding: utf-8 -*-
import unittest
import arky
from arky import cfg
from arky.rest import use as use_network


class TestV2Transaction(unittest.TestCase):

	def __init__(self, *args, **kwargs):
		unittest.TestCase.__init__(self, args, **kwargs)
		try:
			use_network("ark2")
		except:
			raise Exception("Test defined by %s in %s abborted... " % (self.__class__, __file__))
		else:
			self.__tx0 = arky.core.Transaction()

	def test_transaction_getitem(self):
		tx = arky.core.Transaction()
		assert tx["head"] == 0xff
		assert tx["version"] == 0x02
		assert tx["network"] == cfg.marker
		assert tx["type"] == 0x00
		


if __name__ == '__main__':
	unittest.main()
