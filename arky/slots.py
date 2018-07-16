# -*- coding: utf-8 -*-
# © Toons

"""Module to handle computing timestamps for Ark transactions"""

from datetime import datetime, timedelta

import pytz

from arky import cfg

def getTimestamp(**kw):
	"""Get epoch time relative to beginning epoch time."""
	delta = datetime.timedelta(**kw)
	return getTime(datetime.now(pytz.UTC) - delta)


def getTime(time=None):
	"""Get epoch time relative to beginning epoch time."""
	delta = (datetime.now(pytz.UTC) if not time else time) - cfg.begintime
	return delta.total_seconds()


def getRealTime(epoch=None):
	"""Get real time from relative epoch time."""
	epoch = getTime() if epoch is None else epoch
	return cfg.begintime + timedelta(seconds=epoch)


def getSlot(epoch=None):
	"""Get the current slot number."""
	epoch = getTime() if epoch is None else epoch
	return int(epoch // cfg.blocktime)


def getSlotTime(slot):
	"""Get the current slot time."""
	return slot * cfg.blocktime


def getSlotRealTime(slot):
	"""Get real time from the slot's relative epoch time."""
	return getRealTime(slot * cfg.blocktime)


def getLastSlot(slot):
	"""Get the last slot number."""
	return slot + cfg.delegate
