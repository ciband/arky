# -*- encoding: utf8 -*-
# © Toons

from . import cfg

import datetime
import pytz

def getTimestamp(**kw):
	delta = datetime.timedelta(**kw)
	return getTime(datetime.datetime.now(pytz.UTC) - delta)

def getTime(time=None):
	delta = (datetime.datetime.now(pytz.UTC) if not time else time) - cfg.begintime
	return delta.total_seconds()

def getRealTime(epoch=None):
	epoch = getTime() if epoch == None else epoch
	return cfg.begintime + datetime.timedelta(seconds=epoch)

def getSlot(epoch=None):
	epoch = getTime() if epoch == None else epoch
	return int(epoch//cfg.blocktime)

def getSlotTime(slot):
	return slot*cfg.blocktime

def getSlotRealTime(slot):
	return getRealTime(slot*cfg.blocktime)

def getLastSlot(slot):
	return slot + cfg.delegate
