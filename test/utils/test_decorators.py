# -*- coding: utf-8 -*-
import unittest
from arky.utils.decorators import setInterval
from threading import Event
from six import PY3


class TestUtilsDecorators(unittest.TestCase):

	def test_setInterval(self):
		@setInterval(30)
		def testfn():
			print("tick")

		event = testfn()
		assert event.is_set() is False
		if PY3:
			assert isinstance(event, Event)
		else:
			# py2 doesn't support Event object in isinstance
			assert event.__module__ == 'threading'
		event.set()
		assert event.is_set() is True


if __name__ == '__main__':
	unittest.main()
