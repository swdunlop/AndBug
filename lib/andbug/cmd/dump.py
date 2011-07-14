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

import andbug.command, andbug.options

def find_last_method_line(source, first_line):
    for last_line in range(first_line,len(source)):
        if source[last_line][1].startswith('.end method'):
            return last_line
    return False

@andbug.command.action('<class-path> [<method-query>]')
def dump(ctxt, cpath, mquery=None):
    'dumps methods using original sources or apktool sources' 
    cpath, mname, mjni = andbug.options.parse_mquery(cpath, mquery)
    for method in ctxt.sess.classes(cpath).methods(name=mname, jni=mjni):
        source = False
        klass = method.klass.name           

        first_line = method.firstLoc.line
        if first_line is None:
            print '!! could not determine first line of', method
            continue
        
        source = andbug.source.load_source(klass)
        if not source:
            print '!! could not find source for', klass
            continue

        last_line = method.lastLoc.line or find_last_method_line(source, first_line)
        if last_line is False:
            print '!! could not determine last line of', method
            continue

        andbug.source.dump_source(source[first_line:last_line], str(method))