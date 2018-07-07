# -*- coding: utf-8 -*-
# © Toons

import os
import sys
import imp
import logging


__version__ = "1.3.3"

__FROZEN__ = hasattr(sys, "frozen") or hasattr(sys, "importers") or imp.is_frozen("__main__")

if __FROZEN__:
	# if frozen code, HOME and ROOT pathes are same
	ROOT = os.path.normpath(os.path.abspath(os.path.dirname(sys.executable)))
	HOME = ROOT
	FILENAME = os.path.join(ROOT, __name__ + ".log")
else:
	ROOT = os.path.normpath(os.path.abspath(os.path.dirname(__file__)))
	try:
		HOME = os.path.join(os.environ["HOMEDRIVE"], os.environ["HOMEPATH"])
	except:
		HOME = os.environ.get("HOME", ROOT)
	FILENAME = os.path.normpath(os.path.join(HOME, "." + __name__))


# configure logging
logging.basicConfig(level=logging.INFO)
