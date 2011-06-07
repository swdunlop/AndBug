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

import sys
from getopt import getopt
from andbug.process import Process, Failure

import andbug.command

@andbug.command.action('')
def threads(ctxt):
    'lists threads in the process'
    ctxt.proc.suspend()
    try:
        for t in ctxt.proc.threads:
            f = t.frames[0]
            print str(t), f.loc, ('<native>' if f.native else '')
            for k, v in f.values.items():
                print "    ", k, "=", v
    finally:
        ctxt.proc.resume()
