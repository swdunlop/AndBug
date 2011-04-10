from andbug.process import Process, HANDSHAKE_MSG
from unittest import TestCase, main as test_main
from cStringIO import StringIO
import sys

class IoHarness:
	def __init__(self, test, convo):
		self.test = test
		self.readbuf = StringIO(
			"".join(map(lambda x: x[0], convo))
		)
		self.writebuf = StringIO(
			"".join(map(lambda x: x[1], convo))
		)

	def read(self, length):
		return self.readbuf.read(length)

	def write(self, data):
		exp = self.writebuf.read(len(data))
		self.test.assertEqual(exp, data)

class TestProcess(TestCase):
	def test_handshake(self):
		h = IoHarness( self, [
			(HANDSHAKE_MSG, HANDSHAKE_MSG)
		])
		p = Process(h.read, h.write)
		p.start()
		self.assertEqual(True, p.initialized)

if __name__ == '__main__':
	test_main()