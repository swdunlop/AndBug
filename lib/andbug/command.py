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

'''
The andbug.command module underpins the andbug command system by providing 
context and a central registry to command modules in the andbug.cmd package.

Commands for andbug are typically defined as ::

    @andbug.action(
        '<used-argument> [<extra-argument>]'
        (('debug', 'sets the debug level'))
    )
    def sample(ctxt, used, extra=None):
        ...

'''

import os, os.path, sys, getopt, tempfile, inspect, re
import andbug.proto, andbug.vm, andbug.cmd, andbug.source
import traceback
from andbug.util import sh
from time import sleep

#TODO: make short_opts, long_opts, opt_table a dynamic parsing derivative.

OPTIONS = (
    ('pid', 'the process to be debugged, by pid or name'),
    ('dev', 'the device or emulator to be debugged (see adb)'),
    ('src', 'adds a directory where .java or .smali files could be found')
)

class UserError(Exception):
    'indicates an error in how AndBug was used'
    pass

class OptionError(UserError):
    'indicates an error parsing an option supplied to a command'
    pass

class ConfigError(UserError):
    'indicates an error in the configuration of AndBug'
    pass

RE_INT = re.compile('^[0-9]+$')

def seq(*args):
    return args

def adb(*args):
    print 'adb:', repr(args)
    try:
        return sh(seq("adb", *args))
    except OSError as err:
        raise ConfigError('could not find "adb" from the Android SDK in your PATH')

class Context(object):
    '''
    Commands in AndBug are associated with a command Context, which contains
    options and environment information for the command.  This information
    may be reused for multiple commands within the AndBug shell.
    '''

    def __init__(self):
        self.conn = None
        self.sess = None
        self.pid = None
        self.dev = None
        self.shell = False

    def forward(self):
        'constructs an adb forward for the context to access the pid via jdwp'
        temp = tempfile.mktemp()
        cmd = ('-s', self.dev) if self.dev else ()
        cmd += ('forward', 'localfilesystem:' + temp,  'jdwp:%s' % self.pid)
        adb(*cmd)
        return temp

    def connect(self):
        'connects using .forward() to the process associated with this context'
        if self.sess is not None: return
        self.conn = andbug.proto.connect(self.forward())
        self.sess = andbug.vm.Session(self.conn)

    def parseOpts(self, args, options=OPTIONS, proc=True):
        'parse command options in OPTIONS format'
        short_opts = ''.join(opt[0][0] + ':' for opt in options)
        long_opts = list(opt[0] + '=' for opt in options)
        opt_table = {}

        for opt in options:
            opt_table['-' + opt[0][0]] = opt[0]
            opt_table['--' + opt[0]] = opt[0]

        opts, args = getopt.gnu_getopt(args, short_opts, long_opts)

        opts = list((opt_table[k], v) for k, v in opts)
        t = {}
        for k, v in opts: 
            if k == 'src':
                andbug.source.add_srcdir(v)
            else:
                t[k] = v
        
        if proc:
            pid = t.get('pid')
            name = None

            if pid is None:
                pass # do nothing
            elif RE_INT.match(pid):
                pass # continue to do nothing
            else:
                name = pid
                pid = None

            dev = t.get('dev')

            self.findDev(dev)
            self.findPid(dev, pid, name)
        return args, opts

    def findDev(self, dev=None):
        'determines the device for the command based on dev'
        if self.dev is not None: return
        if dev:
            if dev not in map( 
                lambda x: x.split()[0], 
                adb('devices').splitlines()[1:-1]
            ):
                raise OptionError('device serial number not online')
            
            self.dev = dev            
        else:
            if len(adb('devices').splitlines()) != 3:
                raise OptionError(
                    'you must specify a device serial unless there is only'
                    ' one online'
                )
            self.dev = None

        self.dev = dev
    
    def findPid(self, dev=None, pid=None, name=None):
        'determines the process id for the command based on dev, pid and/or name'
        if self.pid is not None: return
        ps = ('shell', 'ps', '-s', dev) if dev else ('shell', 'ps') 
        ps = adb(*ps)
        ps = ps.splitlines()
        head = ps[0]
        ps = (p.split() for p in ps[1:])

        if head.startswith('PID'):
            ps = ((int(p[0]), p[-1]) for p in ps)
        elif head.startswith('USER'):
            ps = ((int(p[1]), p[-1]) for p in ps)
        else:
            raise ConfigError('could not parse "adb shell ps" output')
        
        if pid:
            ps = list(p for p in ps if p[0] == pid)
            if not ps:
                raise OptionError('could not find process ' + pid)
        elif name:
            ps = list(p for p in ps if p[1] == name)
            if not ps:
                raise OptionError('could not find process ' + name)
            pid = ps[0][0]
        else:
            raise OptionError('process pid or name must be specified')

        self.pid = pid

    def can_perform(self, act):
        'uses the act.shell property to determine if it makes sense'
        if self.shell:
            return act.shell != False
        return act.shell != True

    def block_exit(self):
        'prevents termination outside of shells'

        if self.shell:
            # we do not need to block_exit, readline is doing a great
            # job of that for us.
            return

        while True:
            # the purpose of the main thread becomes sleeping forever
            # this is because Python's brilliant threading model only
            # allows the main thread to perceive CTRL-C.
            sleep(3600)
        
    def perform(self, cmd, args):
        'performs the named command with the supplied arguments'
        act = ACTION_MAP.get(cmd)

        if not act:
            print '!! command not supported: "%s."' % cmd
            return False

        if not self.can_perform(act):
            if ctxt.shell:
                print '!! %s is not available in the shell.' % cmd
            else:
                print '!! %s is only available in the shell.' % cmd
            return False

        args, opts = self.parseOpts(args, act.opts, act.proc)
        argct = len(args) + 1 

        if argct < act.min_arity:
            print 'andbug: command "%s" requires more arguments.' % cmd
            return False
        elif argct > act.max_arity:
            print 'andbug: too many arguments for command "%s."' % cmd
            return False

        opts = filter(lambda opt: opt[0] in act.keys, opts)
        kwargs  = {}
        for k, v in opts: 
            kwargs[k] = v

        if act.proc: self.connect()
        try:
            act(self, *args, **kwargs)
        except Exception as exc:
            dump_exc(exc)
            return False

        return True

def dump_exc(exc):       
    tp, val, tb = sys.exc_info()
    with andbug.screed.section("%s: %s" % (tp.__name__, val)):
        for step in traceback.format_tb(tb):
            step = step.splitlines()
            with andbug.screed.item(step[0].strip()):
                for line in step[1:]:
                    andbug.screed.line(line.strip())

ACTION_LIST = []
ACTION_MAP = {}

def bind_action(name, fn):
    ACTION_LIST.append(fn)
    ACTION_MAP[name] = fn

def action(usage, opts = (), proc = True, shell = None):
    'decorates a command implementation with usage and argument information'
    def bind(fn):
        fn.proc = proc
        fn.shell = shell
        fn.usage = usage
        fn.opts = OPTIONS[:] + opts
        fn.keys = list(opt[0] for opt in opts)
        spec = inspect.getargspec(fn)
        defct = len(spec.defaults) if spec.defaults else 0
        argct = len(spec.args) if spec.args else 0
        fn.min_arity = argct - defct
        fn.max_arity = argct
        bind_action(fn.__name__, fn)
    return bind

CMD_DIR_PATH = os.path.abspath(os.path.join( os.path.dirname(__file__), "cmd" ))

def load_commands():
    'loads commands from the andbug.cmd package'
    for name in os.listdir(CMD_DIR_PATH):
        if name.startswith( '__' ):
            continue
        if name.endswith( '.py' ):
            name = 'andbug.cmd.' + name[:-3]
            __import__( name )

def run_command(args, ctxt = None):
    'runs the specified command with a new context'
    if ctxt is None:
        ctxt = Context()
            
    for item in args:
        if item in ('-h', '--help', '-?', '-help'):
            args = ('help', args[0])
            print args
            break
    
    return ctxt.perform(args[0], args[1:])

__all__ = (
    'run_command', 'load_commands', 'action', 'Context', 'OptionError'
)
