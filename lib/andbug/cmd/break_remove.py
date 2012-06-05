## Copyright 2011, Felipe Barriga Richards <spam@felipebarriga.cl>.
##                 All rights reserved.
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

'implementation of the "break-remove" command'

import andbug.command, andbug.screed

@andbug.command.action('<eid/all>', name='break-remove', shell=True)
def break_remove(ctxt, eid):
    'remove hook/breakpoint'
    ctxt.sess.suspend()
    try:
        if eid == 'all':
            with andbug.screed.section('remove all hook'):
                for eid in ctxt.sess.emap.keys():
                    ctxt.sess.emap[eid].clear()
                    andbug.screed.item('Hook <%s> removed' % eid)
        else:
            eid = int(eid)
            if eid in ctxt.sess.emap:
                ctxt.sess.emap[eid].clear()
                andbug.screed.section('Hook <%s> removed' % eid)
            else:
                print '!! error, hook not found. eid=%s' % eid
    finally:
        ctxt.sess.resume()
