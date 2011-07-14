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

from andbug.log import LogReader, LogWriter, LogEvent
from unittest import TestCase, main as test_main
from cStringIO import StringIO
import sys

class TestLog(TestCase):
	def test_log(self):
		def log(time, tag, meta, data):
			o = StringIO()
			w = LogWriter(o)
			evt = LogEvent(time, tag, meta, data)
			sys.stdout.write(str(evt))
			w.writeEvent(evt)
			i = StringIO(o.getvalue())
			r = LogReader(i)
			evt = r.readEvent()
			self.assertEqual(evt.tag, tag)
			self.assertEqual(evt.meta, meta)
			self.assertEqual(evt.time, time)
			self.assertEqual(evt.data, data)
		
		log( 1, "<<<", "META", "" )
		log( 2, ">>>", "META", "the quick brown fox" )

if __name__ == '__main__':
	test_main()