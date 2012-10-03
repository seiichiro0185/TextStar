#!/usr/bin/env python

# Import neccessary modules

from serial import Serial as Serial
from serial.serialutil import SerialException as SerialException
import sys

# Some Constants
TS_CLEAR = chr(12)   # Clear Display
TS_DEL 	 = chr(127)  # Delete Last char
TS_CR    = chr(13)   # Carriage Return
TS_CMD   = chr(254)  # Start command sequence

# Cursor Movement
TS_CUR_UP = chr(11)
TS_CUR_DOWN = chr(10)
TS_CUR_FORW = chr(9)
TS_CUR_BACK = chr(8)
TS_CUR_HOME = chr(254) + chr(72)

# Cursor Styles
TS_CSTYLE_NONE      = 0	# No Cursor
TS_CSTYLE_BLOCK     = 1	# Solid Block
TS_CSTYLE_BLFLASH   = 2	# Flashing Block
TS_CSTYLE_UNDERLINE = 3	# Solid Underline
TS_CSTYLE_UNDFLASH  = 4 # Flashing Underline

# Bargraph Styles
TS_BSTYLE_UNCAPPED = 'B' # Capped Bargraph
TS_BSTYLE_CAPPED   = 'b' # Uncapped Bargraph

# Main Class

class TextStar(object):
	"""
	Class to drive a TextStar Serial 16x2 Display
	"""

	_ser = None  # Internal handel to the serial port
	_dbg = False # Do we want debugging output?

	def _debug(self, message):
		""" Internal debug function """
		if (self._dbg):
			print('TextStar DEBUG: ' + message + '\n')


	def _write(self, command):
		""" Write to Serial, convert string to bytes """
		if (command == None or command == ''):
			return False

		# Translate special characters for display font
		_str = str()
		_transtbl = _str.maketrans('ÄÖÜäöü°', chr(225)+chr(239)+chr(245)+chr(225)+chr(239)+chr(245)+chr(223))
		_cmd = command.translate(_transtbl).encode('iso-8859-1')

		try:
			self._ser.write(_cmd)
			return True
		except:
			self._debug('Error writing to Display')
			raise
			return False


	def _read(self, length=1):
		""" Read from Serial, convert bytes to string """
		_retval = self._ser.read(length)
		if (_retval == None or _retval == ''):
			return None

		return _retval.decode('iso-8859-1')


	def __init__(self, port, baud=9600, debug=False):
		""" Constructor """
		self._dbg = debug

		if (port == None or port == ''):
			self._dbg('No port was given')
			raise ValueError('No Port was given')

		try:
			self._ser = Serial(port, baud, timeout=0.1)
		except SerialException as ex:
			self._debug('Serial connection could not be established: %s' % (ex.args))
			raise

		# Init Display
		self.setCurStyle(TS_CSTYLE_NONE)
		self._write(TS_CLEAR)


	def sendCmd(self, command):
		return self._write(chr(0) + command)


	def setCurStyle(self, style):
		if (style < 0 or style > 4):
			self._debug('Cursor style not valid')

		self._write(chr(0) + TS_CMD + 'C' + chr(style))


	def setCurPos(self, line, column=None):
		if (line < 1 or line > 16):
			self._debug('Invalid line given')
			return(False)

		if (column != None and (column < 1 or column > 16)):
			self._debug('Invalid column given')
			return(False)

		if (column == None):
			return self._write(TS_CMD + 'L' + chr(line))
		else:
			return self._write(TS_CMD + 'P' + chr(line) + chr(column))


	def winScroll(self, updown):
		if (updown < 0 or updown > 1):
			self._debug('Invalid value for up/down')
			return False

		return self._write(TS_CMD + 'O' + chr(updown))


	def drawGraph(self, style, length, percent):
		if (style != 'B' and style != 'b'):
			self._debug('Bargraph style not valid')
			return False

		if (length < 1 or length > 16):
			self._debug('Bargraph length not valid')
			return False

		if (percent < 0 or percent > 100):
			self._debug('Bargraph: invalid percentage')
			return False

		return self._write(TS_CMD + style + chr(length) + chr(percent))

	
	def getKey(self):
		return self._read()
