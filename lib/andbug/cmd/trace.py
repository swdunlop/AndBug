## Copyright 2011, Scott W. Dunlop <swdunlop@gmail.com> All rights reserved.
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

'implementation of the "trace" command'

import andbug.command
from Queue import Queue

@andbug.command.action('<class-path>')
def trace(ctxt, cpath):
    'reports calls to dalvik methods associated with a class'
    q = Queue()    

    cpath = parse_cpath(cpath)
    print '[::] setting hooks'
    for c in ctxt.sess.classes(cpath):
        c.hookEntries(q)
        print '[::] hooked', c
    print '[::] hooks set'

    while True:
        try:
            t = q.get()[0]
            f = t.frames[0]
            print '[::]', t, f.loc
            for k, v in f.values.items():
                print '    ', k, '=', v
        finally:
            t.resume()
