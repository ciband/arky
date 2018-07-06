# -*- coding: utf-8 -*-
import binascii
import struct
from six import PY3


def intasb(i):
	# int as byte conversion
	return unhexlify(hex(i)[2:])


def basint(e):
	# byte as int conversion
	if not PY3:
		e = ord(e)
	return e


def unpack(fmt, fileobj):
	# read value as binary data from buffer
	return struct.unpack(fmt, fileobj.read(struct.calcsize(fmt)))


def pack(fmt, fileobj, value):
	# write value as binary data into buffer
	return fileobj.write(struct.pack(fmt, *value))


def unpack_bytes(f, n):
	# read bytes from buffer
	return unpack("<" + "%ss" % n, f)[0]


def pack_bytes(f, v):
	# write bytes into buffer
	output = pack("!" + "%ss" % len(v), f, (v,))
	return output


def hexlify(data):
	result = binascii.hexlify(data)
	return result.decode()


def unhexlify(data):
	if len(data) % 2:
		data = "0" + data
	result = binascii.unhexlify(data)
	return result if isinstance(result, bytes) else result.encode("utf-8")
