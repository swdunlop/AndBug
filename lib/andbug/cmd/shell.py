#!/usr/bin/env python
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

from __future__ import print_function
import shlex
import andbug.command, andbug.screed

BANNER = 'AndBug (C) 2011 Scott W. Dunlop <swdunlop@gmail.com>'

def input():
    return raw_input('>> ')

def completer(text, state):
    available_commands = andbug.command.ACTION_MAP.keys()
    options = [x for x in available_commands if x.startswith(text)]
    try:
        return options[state]
    except IndexError:
        return None


@andbug.command.action('')
def shell(ctxt):
    'starts the andbug shell with the specified process'
    if not ctxt.shell:
        try:
            import readline
            readline.set_completer(completer)
            readline.parse_and_bind("tab: complete")

        except:
            readline = None
        ctxt.shell = True
        andbug.screed.section(BANNER)

    while True:
        try:
            cmd = shlex.split(input())
        except EOFError:
            return
        andbug.screed.pollcap()
        if cmd:
            andbug.command.run_command(cmd, ctxt=ctxt)
