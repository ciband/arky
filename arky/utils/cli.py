# -*- coding: utf-8 -*-
import sys
import logging
from getpass import getpass


def chooseMultipleItem(msg, *elem):
	n = len(elem)
	if n > 0:
		sys.stdout.write(msg + "\n")
		for i in range(n):
			sys.stdout.write("    %d - %s\n" % (i + 1, elem[i]))
		indexes = []
		while len(indexes) == 0:
			try:
				indexes = input("Choose items: [1-%d or all]> " % n)
				if indexes == "all":
					indexes = [i + 1 for i in range(n)]
				else:
					indexes = [int(s) for s in indexes.strip().replace(" ", ",").split(",") if s != ""]
					indexes = [r for r in indexes if 0 < r <= n]
			except:
				indexes = []
		return indexes
	else:
		sys.stdout.write("Nothing to choose...\n")
		return False


def chooseItem(msg, *elem):
	n = len(elem)
	if n > 1:
		sys.stdout.write(msg + "\n")
		for i in range(n):
			sys.stdout.write("    %d - %s\n" % (i + 1, elem[i]))
		sys.stdout.write("    0 - quit\n")
		i = -1
		while i < 0 or i > n:
			try:
				i = input("Choose an item: [1-%d]> " % n)
				i = int(i)
			except:
				i = -1
		if i == 0:
			# Quit without making a selection
			return False
		return elem[i - 1]
	elif n == 1:
		return elem[0]
	else:
		sys.stdout.write("Nothing to choose...\n")
		return False


def hidenInput(msg):
	"""
	Uses `getpass` built-in which prompts the user without echoing. We check if output is in bytes
	which we have to decode for compatibility reasons
	"""
	data = getpass(msg)
	if isinstance(data, bytes):
		data = data.decode(sys.stdin.encoding)
	return data


def shortAddress(addr, sep="...", n=5):
	"""
	Generates short address used for prompts visual purposes in the CLI eg. "account[DUGvQ...q8G49]"
	"""
	return addr[:n] + sep + addr[-n:]


def prettyfy(dic, tab='\t'):
	result = ""
	if dic:
		maxlen = max([len(e) for e in dic.keys()])
		for k, v in dic.items():
			if isinstance(v, dict):
				result += "{0}{1}:".format(tab, k.ljust(maxlen))
				result += prettyfy(v, tab * 2)
			else:
				result += "{0}{1}: {2}".format(tab, k.rjust(maxlen), v)
			result += "\n"
		return result.encode("ascii", errors="replace").decode()


def prettyPrint(dic, log=True):
	pretty = prettyfy(dic)
	if dic:
		sys.stdout.write("%s" % pretty)
		if log:
			logging.info("\n %s" % pretty.rstrip())
	else:
		sys.stdout.write("\tNothing to print here\n")
		if log:
			logging.info("\tNothing to log here")
