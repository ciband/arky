# -*- encoding: utf8 -*-
# © Toons

import unittest

from arky import rest, cli


class TestUtilDef(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		rest.use("dark")

	def test_unlockAcount(self):
		# function doesn't exist so we can't test it
		pass

	def test_floatAmount(self):
		# can' test because `floatAmount` function still seems to be WIP
		pass


if __name__ == '__main__':
    unittest.main()
