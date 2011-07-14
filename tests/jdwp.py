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

import andbug.jdwp
from unittest import TestCase, main as test_main

def newbuf():
	buf = andbug.jdwp.JdwpBuffer()
	buf.config(1,2,2,4,8) # f, m, o, t, s
	return buf

class TestJdwp(TestCase):
	def test_pack(self):
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
		pack("$", "\0\0\0\4abcd", "abcd")
		
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

	def test_incr_pack(self):
		buf = newbuf()
		buf.packU8(1)
		buf.packU16(1)
		buf.packU32(1)
		buf.packU64(1)
		self.assertEqual(buf.data(), "\1\0\1\0\0\0\1\0\0\0\0\0\0\0\1")		

if __name__ == '__main__':
	test_main()