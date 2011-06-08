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

'implementation of the "help" command'

import andbug.command, andbug.options

@andbug.command.action('<command>', proc=False)
def help(ctxt, cmd):
    'information about how to use andbug'

    act = andbug.command.ACTION_MAP.get(cmd)
    if act is None:
        print 'andbug: there is no command named "%s."' % cmd
        return
    print "USAGE:", cmd, "[-d <dev>] -p <pid>", act.usage 
    print "      ", act.__doc__
