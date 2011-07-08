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

'implementation of the "break" command'

import andbug.command, andbug.screed, andbug.options
from Queue import Queue

def report_hit(t):
    t = t[0]
    with andbug.screed.section("breakpoint hit in %s" % t):
        for f in t.frames:
            name = str(f.loc)
            if f.native:
                name += ' <native>'
            andbug.screed.item(name)

def cmd_break_methods(ctxt, cpath, mpath):
    for c in ctxt.sess.classes(cpath):
        for m in ctxt.sess.methods(mpath):
            l = m.firstLoc
            if l.native:
                andbug.screed.item('Could not hook native %s' % loc)
                continue
            l.hook(func = report_hit)
            andbug.screed.item('Hooked %s' % loc)

def cmd_break_classes(ctxt, cpath):
    for c in ctxt.sess.classes(cpath):
        c.hookEntries(func = report_hit)
        andbug.screed.item('Hooked %s' % c)

@andbug.command.action(
    '<class> [<method>]', name='break', aliases=('b',), shell=True
)
def cmd_break(ctxt, cpath, mquery=None):
    'suspends the process when a method is called'
    cpath, mname, mjni = andbug.options.parse_mquery(cpath, mquery)

    print cpath, mname, mjni
    with andbug.screed.section('Setting Hooks'):
        if mname is None:
            cmd_break_classes(ctxt, cpath)
        else:
            cmd_break_methods(ctxt, cpath, mname, mjni)

    ctxt.block_exit()
