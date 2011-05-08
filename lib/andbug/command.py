import os, os.path, sys, getopt, tempfile, inspect
import andbug.proto, andbug.process, andbug.cmd
from andbug.util import sh

#TODO: make short_opts, long_opts, opt_table a dynamic parsing derivative.

OPTIONS = (
    (int, 'pid', 'the process to be debugged, by pid'),
    (str, 'name', 'the name of the process to be debugged, as found in ps'),
    (str, 'dev', 'the device or emulator to be debugged (see adb)')
)

class OptionError(Exception):
    pass

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

    def parse_opts(self, args, options=OPTIONS):
        short_opts = ''.join(opt[1][0] + ':' for opt in options)
        long_opts = list(opt[1] + '=' for opt in options)
        opt_table = {}

        for opt in options:
                opt_table['-' + opt[1][0]] = opt[0], opt[1]
                opt_table['--' + opt[1]] = opt[0], opt[1]

        t = {}
        opts, args = getopt.gnu_getopt(args, short_opts, long_opts)

        for o, v in opts:
            conv, key = opt_table[o]
            try:
                v = conv(v)
            except:
                v = None
            t[key] = v

        pid = t.get('pid')
        name = t.get('name')
        dev = t.get('dev')

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

        ps = ('adb', 'shell', 'ps', '-s', dev) if dev else ('adb', 'shell', 'ps') 
        
        if pid and name:
            raise OptionError('pid and process name options should not be combined')
        elif pid:
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
        self.dev = dev
        return args

    def perform(self, cmd, args):
        if cmd == 'help':
            list_commands()
            return False
        act = ACTION_MAP.get(cmd)

        if not act:
            print 'andbug: command "%s" not supported.' % cmd
            return False

        args = self.parse_opts(args, act.opts)
        argct = len(args) + 1 
        if argct < act.arity:
            print 'andbug: command "%s" requires more arguments.' % cmd
            return False
        elif argct > act.arity:
            print 'andbug: too many arguments for command "%s."' % cmd
            return False
        else:
            self.connect()
            act(self, *args)
            return True
        
ACTION_LIST = []
ACTION_MAP = {}

def bind_action(name, fn):
    ACTION_LIST.append(fn)
    ACTION_MAP[name] = fn

def action(usage, opts = ()):
    opts = OPTIONS[:] + opts

    def bind(fn):
        fn.usage = usage
        fn.opts = opts
        spec = inspect.getargspec(fn)
        defct = len(spec.defaults) if spec.defaults else 0
        argct = len(spec.args) if spec.args else 0
        fn.arity = argct - defct
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
    return ctxt.perform(args[0], args[1:])

def list_commands():
    print ":: Standard Options ::"
    for t, k, d in OPTIONS:
        print "\t-%s, --%s <%s>  \t%s" % (k[0], k, t.__name__, d)
    print
    print ":: Commands ::"
    for row in ACTION_LIST:
        print "\t%s\t\t\t%s" % (row.__name__, row.__doc__)
    print
    print ":: Examples ::"
    print "\tandbug classes -n com.ioactive.decoy"


