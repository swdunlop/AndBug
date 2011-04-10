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