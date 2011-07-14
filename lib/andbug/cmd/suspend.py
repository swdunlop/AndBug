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

'implementation of the "suspend" command'

import andbug.command, andbug.screed

@andbug.command.action('[<name>]', shell=True)
def suspend(ctxt, name=None):
    'suspends threads in the process'
    if name is None:
        ctxt.sess.suspend()
        return andbug.screed.section('Process Suspended')
    elif name == '*':
        name = None

    with andbug.screed.section('Suspending Threads'):
        for t in ctxt.sess.threads(name):
            t.suspend()
            andbug.screed.item('suspended %s' % t)
