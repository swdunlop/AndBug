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

'implementation of the "help" command'

import andbug.command, andbug.options, andbug.screed

BANNER = 'AndBug (C) 2011 Scott W. Dunlop <swdunlop@gmail.com>'

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

    $ andbug shell [-d <device>] -p <process>.

    The device specification, if omitted, defaults in an identical fashion to
    the ADB debugging bridge command, which AndBug uses heavily.  The process
    specification is either the PID of the process to debug, or the name of
    the process, as found in "adb shell ps."'''

CAUTION = '''
    AndBug is NOT intended for a piracy tool, or other illegal purposes, but 
    as a tool for researchers and developers to gain insight into the 
    implementation of Android applications.  Use of AndBug is at your own risk,
    like most open source tools, and no guarantee of fitness or safety is
    made or implied.'''

SHELL_EXAMPLES = (
    'threads',
    'threads verbose=2',
    'threads "Signal Catcher" verbose=3',
    'classes',
    'classes ioactive',
    'methods com.ioactive.decoy.DecoyActivity onInit',
    'method-trace com.ioactive.decoy.DecoyActivity'
)

CLI_EXAMPLES = (
   'andbug classes -p com.ioactive.decoy',
   'andbug methods -p com.ioactive.decoy com.ioactive.decoy.DecoyActivity onInit'
)

def help_on(ctxt, cmd):
    act = andbug.command.ACTION_MAP.get(cmd)
    if act is None:
        print '!! there is no command named "%s."' % cmd
        return
    if not ctxt.can_perform(act):
        if ctxt.shell:
            print '!! %s is not available in the shell.' % cmd
        else:
            print '!! %s is only available in the shell.' % cmd
        return

    opts = "" if ctxt.shell else " [-d <dev>] -p <pid>"
    usage = "%s%s %s" % (cmd, opts, act.usage)

    if ctxt.shell:
        head = andbug.screed.section(usage)
    else:
        head = andbug.screed.section(BANNER)
        head = andbug.screed.item(usage)
    
    with head:
        andbug.screed.text(act.__doc__)

def general_help(ctxt):
    with andbug.screed.section(BANNER):
        andbug.screed.body(SHELL_INTRO if ctxt.shell else CLI_INTRO)
        andbug.screed.body(CAUTION)
    
    if not ctxt.shell:
        with andbug.screed.section("Options:"):
            for k, d in andbug.command.OPTIONS:
                with andbug.screed.item( "-%s, --%s <opt>" % (k[0], k)):
                    andbug.screed.text(d)

    with andbug.screed.section("Commands:"):
        actions = andbug.command.ACTION_LIST[:]
        actions.sort(lambda a,b: cmp(a.name, b.name))

        for row in actions:
            if ctxt.can_perform(row):
                name  =' | '.join((row.name,) + row.aliases)
                with andbug.screed.item("%s %s" % (name, row.usage)):
                    andbug.screed.text(row.__doc__.strip())

    with andbug.screed.section("Examples:"):
        for ex in (SHELL_EXAMPLES if ctxt.shell else CLI_EXAMPLES):
          andbug.screed.item(ex)

@andbug.command.action('[<command>]', proc=False)
def help(ctxt, topic = None):
    'information about how to use andbug'

    return help_on(ctxt, topic) if topic else general_help(ctxt)
