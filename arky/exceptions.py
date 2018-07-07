# -*- coding: utf-8 -*-
"""
Arky specific exceptions
"""


class ArkyException(Exception):
	"""
	Base exception for all Arky exceptions
	"""


class ParserException(ArkyException):
	"""
	When something goes wrong in the parser method of the CLI class
	"""


class BadPinError(ArkyException):
	"""
	When a bad pin is entered when linking an account with a file
	"""
