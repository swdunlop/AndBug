#!/usr/bin/env python
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

from __future__ import print_function
import shlex
import andbug.command

def output(*data):
    print(*data)

def input():
    return raw_input('>> ')

@andbug.command.action('')
def shell(ctxt):
    'starts the andbug shell with the specified process'
    try:
        import readline
    except:
        readline = None
    
    ctxt.shell = True
    while True:
        try:
            cmd = shlex.split(input())
        except EOFError:
            return
        andbug.command.run_command(cmd, ctxt=ctxt)
