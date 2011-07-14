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

'implementation of the "methods" command'

import andbug.source, os.path

@andbug.command.action('<src-dir>')
def source(ctxt, srcdir):
    'adds a source directory for finding files' 

    if os.path.isdir(srcdir):
        if os.path.isdir(os.path.join(srcdir, "smali")):
            srcdir = os.path.join(srcdir, "smali")
        andbug.source.add_srcdir(srcdir)
    else:
        print '!! directory not found:', repr(srcdir)
