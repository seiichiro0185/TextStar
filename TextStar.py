#!/usr/bin/env python

"""
Module for driving a TextStar Serial 16x2 Module

(C) Stefan Brand 2012
This code is released unter the GPL v3 or later.
"""

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
	Class to drive a TextStar Serial 16x2 Display (Module No CW-LCD-02)
	For in-depth information about the display see the datasheet at http://cats-whisker.com/resources/documents/cw-lcd-02_datasheet.pdf
	"""

	_ser = None  # Internal handel to the serial port
	_dbg = False # Do we want debugging output?

	def _debug(self, message):
		""" Internal debug function """
		if (self._dbg):
			print('TextStar DEBUG: ' + message + '\n')


	def _write(self, command):
		""" Write to Serial, convert string to bytes and convert characters """
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
		"""
		Constructor, initializes a new instance of the display class. Takes the following Arguments:

		port:
			Serial Port to use. On linux this can be '/dev/ttyS0' or '/dev/ttyUSB0' for example

		baud: [optional]
			baudrate to use. Defaults to 9600 Baud, should match the rate set in the display

		debug: [optional]
			If set to True debugging / errormessages are print to STDERR. Default value is False.

		Example:

		from TextStar import *
		display = TextStar('/dev/ttyAMA0', debug=True)
		
		Import the module and initialize a new instance using the RaspberryPi Serial port. Debugging output to STDERR is enabled.
		"""
		self._dbg = debug

		if (port == None or port == ''):
			self._dbg('No port was given')
			raise ValueError('No Port was given')

		try:
			self._ser = Serial(port, baud, timeout=0.1)
		except SerialException as ex:
			self._debug('Serial connection could not be established: %s' % (ex.args))
			raise

		# Initialize display Display
		self.setCurStyle(TS_CSTYLE_NONE)
		self._write(TS_CLEAR)


	def sendCmd(self, command):
		""" 
		Send text or commands to the display 

		Example:
			TextStar.sendCmd(TS_CLEAR)
			TextStar.sendCmd('Hello World!')

			Clear the display and show the Text 'Hello World!'
		"""
		return self._write(chr(0) + command)


	def setCurStyle(self, style):
		""" 
		Sets the Cursor Style. The following Styles are supported:
			TS_CSTYLE_NONE      - No Cursor
			TS_CSTYLE_BLOCK     - Solid Block Cursor
			TS_CSTYLE_BLFLASH   - Flashing Block Cursor
			TS_CSTYLE_UNDERLINE - Solid Underline Cursor
			TS_CSTYLE_UNDFLASH  - Flashing Underline Cursor

		Example:
			TextStar.setCursorStyle(TS_CSTYLE_BLOCK) 

			Set the Cursor to a solid Block
		"""

		if (style < 0 or style > 4):
			self._debug('Cursor style not valid')

		self._write(chr(0) + TS_CMD + 'C' + chr(style))


	def setCurPos(self, line, column=None):
		"""
		Position the cursor at the specified Position. Uses the Following Arguments:

		line:
			line number to set the Cursor. The display has 16 virtual lines, so this value can range from 1 to 16.
			Only 2 lines are shown at any time (which lines depends on the position of the Window.

		column: [Optional]
			Column number to position the Cursor at. If this argument is omitted the column 1 is assumed.
			The values can range from 1 to 16.

		Example:
			TextStar.setCurPos(2, 4)

			Position the curor at line 2, column 4
		"""

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
		"""
		Move the window up or down 1 line. Takes the following Arguments:
		
		updown:
			Determines in which direction to move the window.
			0 - Move down one line
			1 - move up one line
		"""

		if (updown < 0 or updown > 1):
			self._debug('Invalid value for up/down')
			return False

		return self._write(TS_CMD + 'O' + chr(updown))


	def drawGraph(self, style, length, percent):
		"""
			Draws a bar graph using the displays bar graph feature. Takes the following arguments:

			style:
				The style of the bar graph, the following styles are supported:
					TS_BSTYLE_CAPPED   - Capped (terminated) bar graph
					TS_BSTYLE_UNCAPPED - Uncapped (unterminated) bar graph

			length:
				Length of the whole graph in characters. Can range from 1 to 16.

			percent:
				Percentage of the graph that will be filled.

			Example:
				TextStar.drawGraph(TS_BSTYLE_CAPPED, 8, 65)

				Draw a terminated graph using 8 characters and filled to 65 %
		"""

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
		"""
			Query for the displays Keys. Takes no Arguments.
			The method will wait 0.1 seconds for a keypress and return None if no key was pressed.
			The Keys can be configured in the display. Standard keys are A, B, C and D.
			For every key the uppercase letter is returned on key down and the lowercase letter is returned on key release
		"""
		return self._read()
