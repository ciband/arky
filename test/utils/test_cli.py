# -*- coding: utf-8 -*-
import io

import unittest

from collections import OrderedDict
from mock import patch

from arky.utils.cli import prettyPrint, shortAddress, chooseItem, chooseMultipleItem


class TestUtilsCLI(unittest.TestCase):

	def test_prettyPrint(self):
		# we use OrderedDict to always guarantee the same order as a result so we can assert it
		data = OrderedDict()
		data["testing"] = True
		data["transactions"] = "many"
		with patch('sys.stdout', new=io.StringIO()) as stdout:
			prettyPrint(data, log=False)
		assert stdout.getvalue() == '\t     testing: True\n\ttransactions: many\n'

	def test_shortAddress(self):
		output = shortAddress("DUGvQBxLzQqrNy68asPcU3stWQyzVq8G49")
		assert output == "DUGvQ...q8G49"

	@patch('arky.utils.cli.input', return_value="2")
	def test_chooseItem(self, input):
		output = chooseItem("Network(s) found:", *["ark", "dark", "lisk"])
		assert output == "dark"

	@patch('arky.utils.cli.input', return_value="0")
	def test_chooseItemQuit(self, input):
		output = chooseItem("Network(s) found:", *["ark", "dark", "lisk"])
		assert output == False

	def test_chooseMultipleItem(self):
		scenarios = [
			("1, 2", [1, 2]),
			("all", [1, 2, 3])
		]
		for input_value, expected in scenarios:
			with patch('arky.utils.cli.input') as mocked_input:
				mocked_input.return_value = input_value
				output = chooseMultipleItem("Transactions(s) found:", *["first", "second", "third"])
			assert output == expected


if __name__ == '__main__':
	unittest.main()
