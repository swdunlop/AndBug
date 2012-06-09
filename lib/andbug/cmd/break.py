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

'implementation of the "break" command'

import andbug.command, andbug.screed, andbug.options
from Queue import Queue

def report_hit(t):
    t = t[0]
    with andbug.screed.section("Breakpoint hit in %s, process suspended." % t):
        t.sess.suspend()
        for f in t.frames:
            name = str(f.loc)
            if f.native:
                name += ' <native>'
            andbug.screed.item(name)

def cmd_break_methods(ctxt, cpath, mpath):
    for c in ctxt.sess.classes(cpath):
        for m in c.methods(mpath):
            l = m.firstLoc
            if l.native:
                andbug.screed.item('Could not hook native %s' % l)
                continue
            h = l.hook(func = report_hit)
            andbug.screed.item('Hooked %s' % h)

def cmd_break_classes(ctxt, cpath):
    for c in ctxt.sess.classes(cpath):
        h = c.hookEntries(func = report_hit)
        andbug.screed.item('Hooked %s' % h)

def cmd_break_line(ctxt, cpath, mpath, line):
    for c in ctxt.sess.classes(cpath):
        for m in c.methods(mpath):
            l = m.lineTable
            if l is None or len(l) <= 0:
                continue
            if line == 'show':
                andbug.screed.item(str(sorted(l.keys())))
                continue
            l = l.get(line, None)
            if l is None:
                andbug.screed.item("can't found line %i" % line)
                continue
            if l.native:
                andbug.screed.item('Could not hook native %s' % l)
                continue
            h = l.hook(func = report_hit)
            andbug.screed.item('Hooked %s' % h)

@andbug.command.action(
    '<class> [<method>] [show/lineNo]', name='break', aliases=('b',), shell=True
)
def cmd_break(ctxt, cpath, mquery=None, line=None):
    'set breakpoint'
    cpath, mname, mjni = andbug.options.parse_mquery(cpath, mquery)
    if line is not None:
        if line != 'show':
            line = int(line)

    with andbug.screed.section('Setting Hooks'):
        if mname is None:
            cmd_break_classes(ctxt, cpath)
        elif line is None:
            cmd_break_methods(ctxt, cpath, mname)
        else:
            cmd_break_line(ctxt, cpath, mname, line)

    ctxt.block_exit()
