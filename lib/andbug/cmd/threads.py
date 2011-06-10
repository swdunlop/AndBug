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

'implementation of the "threads" command'

import andbug.command, andbug.screed

@andbug.command.action('')
def threads(ctxt):
    'lists threads in the process'
    ctxt.sess.suspend()

    try:
        for t in ctxt.sess.threads:
            with andbug.screed.section(str(t)):
                for f in t.frames:
                    name = str(f.loc)
                    if f.native:
                        name += ' <native>'
                    with andbug.screed.item(name):
                        for k, v in f.values.items():
                            andbug.screed.item( "%s=%s" %(k, v))
    finally:
        ctxt.sess.resume()
