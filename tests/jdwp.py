import andbug.jdwp
from unittest import TestCase, main as test_main

class TestJdwp(TestCase):

	def test_pack(self):
		def newbuf():
			buf = andbug.jdwp.JdwpBuffer()
			buf.config(1,2,2,4,8) # f, m, o, t, s
			return buf

		def pack(fmt, pkt, *data):
			print ":: %r of %r -> %r" % (fmt, data, pkt)
			data = list(data)
			buf = newbuf()
			res = buf.pack(fmt, *data)
			self.assertEqual(res, pkt)
			
			buf = newbuf()
			res = buf.unpack(fmt, pkt)
			self.assertEqual(res, data)

		pack("", "")
		pack("1", "\0", 0)
		pack("2", "\0\1", 1)
		pack("4", "\0\0\0\1", 1)
		pack("8", "\0\0\0\0\0\0\0\1", 1)
		pack("f", "\1", 1)
		pack("m", "\0\1", 1)
		pack("o", "\0\1", 1)
		pack("t", "\0\0\0\1", 1)
		pack("s", "\0\0\0\0\0\0\0\1", 1)

		pack("1248", (
			"\0"
			"\0\1"
			"\0\0\0\1"
			"\0\0\0\0\0\0\0\1"
		), 0, 1, 1, 1)

		pack("fmots", (
			"\0"
			"\0\1"
			"\0\1"
			"\0\0\0\1"
			"\0\0\0\0\0\0\0\1"
		), 0, 1, 1, 1, 1)


if __name__ == '__main__':
	test_main()