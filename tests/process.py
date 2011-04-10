from andbug.process import Process, HANDSHAKE_MSG, IDSZ_REQ
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

class TestProcess(TestCase):
	def test_start(self):
		h = IoHarness( self, [
			(HANDSHAKE_MSG, HANDSHAKE_MSG),
			(IDSZ_REQ, IDSZ_RES)
		])
		p = Process(h.read, h.write)
		p.start()
		self.assertEqual(True, p.initialized)

if __name__ == '__main__':
	test_main()