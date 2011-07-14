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

'''
The andbug.proto module abstracts the JDWP wire protocol into a more 
manageable request/response API using an input worker thread in the
background and a number of mutexes to control contests for output.
'''

import socket, tempfile
import andbug.util
from threading import Thread, Lock
from andbug.jdwp import JdwpBuffer
from Queue import Queue, Empty as EmptyQueue

class EOF(Exception):
    'signals that an EOF has been encountered'
    def __init__(self, inner = None):
        Exception.__init__(
            self, str(inner) if inner else "EOF"
        )

class HandshakeError(Exception):
    'signals that the JDWP handshake failed'
    def __init__(self):
        Exception.__init__(
            self, 'handshake error, received message did not match'
        )

class ProtocolError(Exception):
    pass

HANDSHAKE_MSG = 'JDWP-Handshake'
HEADER_FORMAT = '4412'
IDSZ_REQ = (
    '\x00\x00\x00\x0B' # Length
    '\x00\x00\x00\x01' # Identifier
    '\x00'             # Flags
    '\x01\x07'         # Command 1:7
)

def forward(pid, dev=None):
    'constructs an adb forward for the context to access the pid via jdwp'
    if dev:
        dev = andbug.util.find_dev(dev)
    pid = andbug.util.find_pid(pid)
    temp = tempfile.mktemp()
    cmd = ('-s', dev) if dev else ()
    cmd += ('forward', 'localfilesystem:' + temp,  'jdwp:%s' % pid)
    andbug.util.adb(*cmd)
    return temp

def connect(addr, portno = None, trace=False):
    'connects to an AF_UNIX or AF_INET JDWP transport'
    if addr and portno:
        conn = socket.create_connection((addr, portno))
    elif isinstance(addr, int):
        conn = socket.create_connection(('127.0.0.1', addr))
    else:
        conn = socket.socket(socket.AF_UNIX)
        conn.connect(addr)

    def read(amt):
        'read wrapper internal to andbug.proto.connect'
        req = amt
        buf = ''
        while req:
            pkt = conn.recv(req)
            if not pkt: raise EOF()
            buf += pkt
            req -= len(pkt)
        if trace:
            print ":: RECV:", repr(buf)
        return buf 
    
    def write(data):
        'write wrapper internal to andbug.proto.connect'
        try:
            if trace:
                print ":: XMIT:", repr(data)
            conn.sendall(data)
        except Exception as exc:
            raise EOF(exc)
        
    p = Connection(read, write)
    p.start()
    return p

class Connection(Thread):
    '''
    The JDWP Connection is a thread which abstracts the asynchronous JDWP protocol
    into a more synchronous one.  The thread will listen for packets using the
    supplied read function, and transmit them using the write function.  

    Requests are sent by the processor using the calling thread, with a mutex 
    used to protect the write function from concurrent access.  The requesting
    thread is then blocked waiting on a response from the processor thread.

    The Connectionor will repeatedly use the read function to receive packets, which
    will be dispatched based on whether they are responses to a previous request,
    or events.  Responses to requests will cause the requesting thread to be
    unblocked, thus simulating a synchronous request.
    '''

    def __init__(self, read, write):
        Thread.__init__(self)
        self.xmitbuf = JdwpBuffer()
        self.recvbuf = JdwpBuffer()
        self._read = read
        self.write = write
        self.initialized = False
        self.next_id = 3
        self.bindqueue = Queue()
        self.qmap = {}
        self.rmap = {}
        self.xmitlock = Lock()

    def read(self, sz):
        'read size bytes'
        if sz == 0: return ''
        pkt = self._read(sz)
        if not len(pkt): raise EOF()
        return pkt

    ###################################################### INITIALIZATION STEPS
    
    def writeIdSzReq(self):
        'write an id size request'
        return self.write(IDSZ_REQ)

    def readIdSzRes(self):
        'read an id size response'
        head = self.readHeader()
        if head[0] != 20:
            raise ProtocolError('expected size of an idsize response')
        if head[2] != 0x80:
            raise ProtocolError(
                'expected first server message to be a response'
            )
        if head[1] != 1:
            raise ProtocolError('expected first server message to be 1')

        sizes = self.recvbuf.unpack( 'iiiii', self.read(20) )
        self.sizes = sizes
        self.recvbuf.config(*sizes)
        self.xmitbuf.config(*sizes)
        return None

    def readHandshake(self):
        'read the jdwp handshake'
        data = self.read(len(HANDSHAKE_MSG))
        if data != HANDSHAKE_MSG:
            raise HandshakeError()
        
    def writeHandshake(self):
        'write the jdwp handshake'
        return self.write(HANDSHAKE_MSG)

    ############################################### READING / PROCESSING PACKETS
    
    def readHeader(self):
        'reads a header and returns [size, id, flags, event]'
        head = self.read(11)
        data = self.recvbuf.unpack(HEADER_FORMAT, head)
        data[0] -= 11
        return data
    
    def process(self):
        'invoked repeatedly by the processing thread'

        size, ident, flags, code = self.readHeader() #TODO: HANDLE CLOSE
        data = self.read(size) #TODO: HANDLE CLOSE
        try: # We process binds after receiving messages to prevent a race
            while True:
                self.processBind(*self.bindqueue.get(False))
        except EmptyQueue:
            pass

        #TODO: update binds with all from bindqueue
        
        if flags == 0x80:
            self.processResponse(ident, code, data)
        else:
            self.processRequest(ident, code, data)

    def processBind(self, qr, ident, chan):
        'internal to i/o thread; performs a query or request bind'
        if qr == 'q':
            self.qmap[ident] = chan
        elif qr == 'r':
            self.rmap[ident] = chan

    def processRequest(self, ident, code, data):
        'internal to the i/o thread w/ recv ctrl; processes incoming request'
        chan = self.rmap.get(code)
        if not chan: return #TODO
        buf = JdwpBuffer()
        buf.config(*self.sizes)
        buf.prepareUnpack(data)
        return chan.put((ident, buf))
        
    def processResponse(self, ident, code, data):
        'internal to the i/o thread w/ recv ctrl; processes incoming response'
        chan = self.qmap.pop(ident, None)
        if not chan: return
        buf = JdwpBuffer()
        buf.config(*self.sizes)
        buf.prepareUnpack(data)
        return chan.put((code, buf))

    def hook(self, code, chan):
        '''
        when code requests are received, they will be put in chan for
        processing
        '''

        with self.xmitlock:
            self.bindqueue.put(('r', code, chan))
        
    ####################################################### TRANSMITTING PACKETS
    
    def acquireIdent(self):
        'used internally by the processor; must have xmit control'
        ident = self.next_id
        self.next_id += 2
        return ident

    def writeContent(self, ident, flags, code, body):
        'used internally by the processor; must have xmit control'

        size = len(body) + 11
        self.xmitbuf.preparePack(11)
        data = self.xmitbuf.pack(
            HEADER_FORMAT, size, ident, flags, code
        )
        self.write(data)
        return self.write(body)

    def request(self, code, data='', timeout=None):
        'send a request, then waits for a response; returns response'
        queue = Queue()

        with self.xmitlock:
            ident = self.acquireIdent()
            self.bindqueue.put(('q', ident, queue))
            self.writeContent(ident, 0x0, code, data)
        
        try:
            return queue.get(1, timeout)
        except EmptyQueue:
            return None

    def buffer(self):
        'returns a JdwpBuffer configured for this connection'
        buf = JdwpBuffer()
        buf.config(*self.sizes)
        return buf
        
    ################################################################# THREAD API
    
    def start(self):
        'performs handshaking and solicits configuration information'
        self.daemon = True

        if not self.initialized:
            self.writeHandshake()
            self.readHandshake()
            self.writeIdSzReq()
            self.readIdSzRes()
            self.initialized = True
            Thread.start(self)
        return None

    def run(self):
        'runs forever; overrides the default Thread.run()'
        try:
            while True:
                self.process()
        except EOF:
            return
    
