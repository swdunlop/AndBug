import os, os.path, sys, getopt, tempfile, inspect, re
import andbug.proto, andbug.process, andbug.cmd
from andbug.util import sh

#TODO: make short_opts, long_opts, opt_table a dynamic parsing derivative.

OPTIONS = (
    ('pid', 'the process to be debugged, by pid or name'),
    ('dev', 'the device or emulator to be debugged (see adb)')
)

class OptionError(Exception):
    pass

RE_INT = re.compile('^[0-9]+$')

class Context(object):
    def __init__(self):
        self.conn = None
        self.proc = None

    def forward(self):
        temp = tempfile.mktemp()
        cmd = ['adb', '-s', self.dev] if self.dev else ['adb']
        cmd += ['forward', 'localfilesystem:' + temp,  'jdwp:' + self.pid]
        sh(cmd)
        return temp

    def connect(self):
        self.conn = andbug.proto.connect(self.forward())
        self.proc = andbug.process.Process(self.conn)

    def parse_opts(self, args, options=OPTIONS, proc=True):
        short_opts = ''.join(opt[0][0] + ':' for opt in options)
        long_opts = list(opt[0] + '=' for opt in options)
        opt_table = {}

        for opt in options:
                opt_table['-' + opt[0][0]] = opt[0]
                opt_table['--' + opt[0]] = opt[0]

        opts, args = getopt.gnu_getopt(args, short_opts, long_opts)

        opts = list((opt_table[k], v) for k, v in opts)
        t = {}
        for k, v in opts: t[k] = v
        
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

            self.find_dev(dev)
            self.find_pid(dev, pid, name)
        return args, opts

    def find_dev(self, dev=None):
        if dev:
            if dev not in map( 
                lambda x: x.split()[0], 
                sh(('adb', 'devices')).splitlines()[1:-1]
            ):
                raise OptionError('device serial number not online')
            
            self.dev = dev            
        else:
            if len(sh(('adb', 'devices')).splitlines()) != 3:
                raise OptionError(
                    'you must specify a device serial unless there is only one online'
                )
            self.dev = None

        self.dev = dev
    
    def find_pid(self, dev=None, pid=None, name=None):
        ps = ('adb', 'shell', 'ps', '-s', dev) if dev else ('adb', 'shell', 'ps') 

        if pid:
            if pid not in map( 
                lambda x: x.split()[1], 
                sh(('adb', 'shell', 'ps')).splitlines()[1:]
            ):
                raise OptionError('could not find process ' + pid)
        elif name:
            rows = filter( 
                lambda x: x.split()[-1] == name, 
                sh(('adb', 'shell', 'ps')).splitlines()[1:]
            )

            if not rows:
                raise OptionError('could not find process ' + name)
            pid = rows[0].split()[1]
        else:
            raise OptionError('process pid or name must be specified')

        self.pid = pid

    def perform(self, cmd, args):
        act = ACTION_MAP.get(cmd)

        if not act:
            print 'andbug: command "%s" not supported.' % cmd
            return False

        args, opts = self.parse_opts(args, act.opts, act.proc)
        argct = len(args) + 1 

        if argct < act.min_arity:
            print 'andbug: command "%s" requires more arguments.' % cmd
            return False
        elif argct > act.max_arity:
            print 'andbug: too many arguments for command "%s."' % cmd
            return False

        opts = filter(lambda opt: opt[0] in act.keys, opts)        
        kwargs  = {}
        for k, v in opts: kwargs[k] = v

        if act.proc: self.connect()
        act(self, *args, **kwargs)
        return True
        
ACTION_LIST = []
ACTION_MAP = {}

def bind_action(name, fn):
    ACTION_LIST.append(fn)
    ACTION_MAP[name] = fn

def action(usage, opts = (), proc = True):
    def bind(fn):
        fn.proc = proc
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
    import pkgutil, andbug.cmd
    for name in os.listdir(CMD_DIR_PATH):
        if name.startswith( '__' ):
            continue
        if name.endswith( '.py' ):
            name = 'andbug.cmd.' + name[:-3]
            __import__( name )

def run_command(args):
    ctxt = Context()
    ix = 0
    for item in args:
            if item in ('-h', '--help', '-?', '-help'):
                    args = ('help', args[0])
                    print args
                    break
            ix += 1
    return ctxt.perform(args[0], args[1:])
