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

COPYRIGHT = '   AndBug (C) 2011 Scott W. Dunlop <swdunlop@gmail.com>'

SHELL_INTRO = '''
   The AndBug shell is a simple interactive console shell that reduces typing
   and overhead involved in setting up a debugging session.  Commands entered
   at the prompt will be evaluated using the current device and process as a
   context.  Where possible, AndBug uses readline; if your Python
   install lacks readline, this shell will be more difficult to use due to
   the poor console I/O functionality in vanilla Python.  (The "rlwrap" 
   utility may help.)'''

CLI_INTRO = '''
   AndBug is a reverse-engineering debugger for the Android Dalvik virtual
   machine employing the Java Debug Wire Protocol (JDWP) to interact with
   Android applications without the need for source code.  The majority of
   AndBug's commands require the context of a connected Android device and
   a specific Android process to target, which should be specified using the
   -d and -p options.

   The debugger offers two modes -- interactive and noninteractive, and a
   comprehensive Python API for writing debugging scripts.  The interactive
   mode is accessed using:

   -- andbug shell [-d <device>] -p <process>.

   The device specification, if omitted, defaults in an identical fashion to
   the ADB debugging bridge command, which AndBug uses heavily.  The process
   specification is either the PID of the process to debug, or the name of
   the process, as found in "adb shell ps."'''

CAUTION = '''
   AndBug is NOT intended as a piracy tool, or illegal purposes, but as a 
   tool for researchers and developers to gain insight into the 
   implementation of Android applications.  Use of AndBug is at your own risk,
   like most open source tools, and no guarantee of fitness or safety is
   made or implied.'''

def help_on(ctxt, cmd):
    act = andbug.command.ACTION_MAP.get(cmd)
    if act is None:
        print 'andbug: there is no command named "%s."' % cmd
        return

    opts = "" if ctxt.shell else "[-d <dev>] -p <pid>"
    print "   ##", cmd, opts, act.usage
    print "     ", act.__doc__

def general_help(ctxt):
    print COPYRIGHT
    if ctxt.shell:
        print SHELL_INTRO
    else:
        print CLI_INTRO
    
    print CAUTION
    print

    if not ctxt.shell:
        print "   ## Options"
        for k, d in andbug.command.OPTIONS:
            print "   -- -%s, --%s <opt>  \t%s" % (k[0], k, d)
        print
    
    print "   ## Commands"
    for row in andbug.command.ACTION_LIST:
        print "   -- %s %s" % (row.__name__, row.usage)
        print "     ", row.__doc__
    print

    if ctxt.shell:
        print "   ## Examples"
        print "   -- classes"
        print "   -- methods com.ioactive.decoy.DecoyActivity onInit"
    else:
        print "   ## Examples"
        print "   -- andbug classes -p com.ioactive.decoy"
        print "   -- andbug methods -p com.ioactive.decoy com.ioactive.decoy.DecoyActivity onInit"

@andbug.command.action('[<command>]', proc=False)
def help(ctxt, topic = None):
    'information about how to use andbug'

    return help_on(ctxt, topic) if topic else general_help(ctxt)

