# -*- coding: utf-8 -*-
import threading


def setInterval(interval):
	""" threaded decorator
	>>> @setInterval(10)
	... def tick():
	...     print("Tick")
	>>> event = tick() # print 'Tick' every 10 sec
	>>> type(event)
	<class 'threading.Event'>
	>>> event.set() # stop printing 'Tick' every 10 sec
	"""
	def decorator(function):
		def wrapper(*args, **kwargs):
			stopped = threading.Event()

			# executed in another thread
			def loop():
				# until stopped
				while not stopped.wait(interval):
					function(*args, **kwargs)

			t = threading.Thread(target=loop)
			# stop if the program exits
			t.daemon = True
			t.start()
			return stopped
		return wrapper
	return decorator
