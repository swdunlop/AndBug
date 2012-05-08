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

'implementation of the "thread trace" command'

import andbug.command, andbug.screed, andbug.options
from Queue import Queue

def report_hit(t):
    t = t[0]
    try:
        with andbug.screed.section("trace %s" % t):
            for f in t.frames:
                name = str(f.loc)
                if f.native:
                    name += ' <native>'
                with andbug.screed.item(name):
                    for k, v in f.values.items():
                        andbug.screed.item( "%s=%s" %(k, v))
    finally:
        t.resume()

@andbug.command.action('<thread-name>', aliases=('tt','ttrace'))

def thread_trace(ctxt, tname=None):
	'reports calls to specific thread in the process'
	ctxt.sess.suspend()
	with andbug.screed.section('Setting Hooks'):
		try:
			for t in ctxt.sess.threads(tname):
				t.hook(func = report_hit)
				andbug.screed.item('Hooked %s' % t)
		finally:
			ctxt.sess.resume()
