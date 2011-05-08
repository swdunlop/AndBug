import os, os.path, sys, getopt, tempfile, imp
import andbug.proto, andbug.process, andbug.cmd
from andbug.util import sh

OPTIONS = (
    (int, 'pid', 'the process to be debugged, by pid'),
    (str, 'name', 'the name of the process to be debugged, as found in ps'),
    (str, 'dev', 'the device or emulator to be debugged (see adb)')
)

SHORT_OPTS = ''.join(opt[1][0] + ':' for opt in OPTIONS)
LONG_OPTS = list(opt[1] + '=' for opt in OPTIONS)
OPT_TABLE = {}

for opt in OPTIONS:
        OPT_TABLE['-' + opt[1][0]] = opt[0], opt[1]
        OPT_TABLE['--' + opt[1]] = opt[0], opt[1]

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

    def parse_opts(self, args):
        t = {}
        opts, args = getopt.gnu_getopt(args, SHORT_OPTS, LONG_OPTS)

        for o, v in opts:
            conv, key = OPT_TABLE[o]
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
            print "andbug: command %s not supported." % cmd
            return False

        args = self.parse_opts(args)
        self.connect()
        act(self, *args)
        return True
        
ACTION_LIST = []
ACTION_MAP = {}

def bind_action(name, fn):
    ACTION_LIST.append(fn)
    ACTION_MAP[name] = fn
    print ACTION_MAP

def action(usage):
    def bind(fn):
        fn.usage = usage
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


