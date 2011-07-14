## Copyright 2011, IOActive, Inc. All rights reserved.
##
## AndBug is free software: you can redistribute it and/or modify it under 
## the terms of version 3 of the GNU Lesser General Public License as 
## published by the Free Software Foundation.
##
## AndBug is distributed in the hope that it will be useful, but WITHOUT ANY
## WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS 
## FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for 
## more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with AndBug.  If not, see <http://www.gnu.org/licenses/>.

from andbug.proto import Connection, HANDSHAKE_MSG, IDSZ_REQ
from unittest import TestCase, main as test_main
from cStringIO import StringIO
import sys

IDSZ_RES = (
	'\x00\x00\x00\x1F' # Length
	'\x00\x00\x00\x01' # Identifier
	'\x80'             # Response
	'\x00\x00'         # Not an error

	'\x00\x00\x00\x01' # F-Sz
	'\x00\x00\x00\x02' # M-Sz
	'\x00\x00\x00\x02' # O-Sz
	'\x00\x00\x00\x04' # T-Sz
	'\x00\x00\x00\x08' # S-Sz
)

class IoHarness:
	def __init__(self, test, convo):
		self.test = test
		self.readbuf = StringIO(
			"".join(map(lambda x: x[1], convo))
		)
		self.writebuf = StringIO(
			"".join(map(lambda x: x[0], convo))
		)

	def read(self, length):
		return self.readbuf.read(length)

	def write(self, data):
		exp = self.writebuf.read(len(data))
		self.test.assertEqual(exp, data)

def make_conn(harness):
	conn = Connection(harness.read, harness.write)
	conn.start()
	return conn

SAMPLE_REQ = (
	'\x00\x00\x00\x0B' # Length
	'\x00\x00\x00\x03' # Identifier
	'\x00'             # Request
	'\x42\x42'         # Not an error
)

SAMPLE_RES = (
	'\x00\x00\x00\x0B' # Length
	'\x00\x00\x00\x03' # Identifier
	'\x80'             # Response
	'\x00\x00'         # Success
)

class TestConnection(TestCase):
	def test_start(self):
		h = IoHarness( self, [
			(HANDSHAKE_MSG, HANDSHAKE_MSG),
			(IDSZ_REQ, IDSZ_RES)
		])
		p = make_conn(h)
		self.assertEqual(True, p.initialized)

if __name__ == '__main__':
	test_main()
