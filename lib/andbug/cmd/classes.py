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

'implementation of the "classes" command'

import andbug.command, andbug.screed

@andbug.command.action('[<partial class name>]')
def classes(ctxt, expr=None):
    'lists loaded classes. if no partial class name supplied, list all classes.'
    with andbug.screed.section('Loaded Classes'):
        for c in ctxt.sess.classes():
            n = c.jni
            if n.startswith('L') and n.endswith(';'):
                n = n[1:-1].replace('/', '.')
            else:
                continue

            if expr is not None:
                if n.find(expr) >= 0:
                    andbug.screed.item(n)
            else:
                andbug.screed.item(n)

