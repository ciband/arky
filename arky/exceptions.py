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
