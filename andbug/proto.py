## Copyright 2011, Scott W. Dunlop <swdunlop@gmail.com> All rights reserved.
##
## Redistribution and use in source and binary forms, with or without 
## modification, are permitted provided that the following conditions are 
## met:
## 
##    1. Redistributions of source code must retain the above copyright 
##       notice, this list of conditions and the following disclaimer.
## 
##    2. Redistributions in binary form must reproduce the above copyright 
##       notice, this list of conditions and the following disclaimer in the
##       documentation and/or other materials provided with the distribution.
## 
## THIS SOFTWARE IS PROVIDED BY SCOTT DUNLOP 'AS IS' AND ANY EXPRESS OR 
## IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
## OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. 
## IN NO EVENT SHALL SCOTT DUNLOP OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
## INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES 
## (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
## SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) 
## HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, 
## STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
## ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
## POSSIBILITY OF SUCH DAMAGE.

import socket
from threading import Thread, Lock
from andbug.jdwp import JdwpBuffer
from Queue import Queue, Empty as EmptyQueue

class EOF(Exception):
	def __init__(self, inner = None):
		Exception.__init__(
			self, str(inner) if inner else "EOF"
		)

class HandshakeError(Exception):
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

def connect(addr, portno, trace=False):
	conn = socket.create_connection((addr, portno))

	def read(amt):
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
	The JDWP Connectionor is a thread which abstracts the asynchronous JDWP protocol
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
		self.nextId = 3
		self.bindqueue = Queue()
		self.qmap = {}
		self.rmap = {}
		self.xmitlock = Lock()

	def read(self, sz):
		if sz == 0: return ''
		pkt = self._read(sz)
		if not len(pkt): raise EOF()
		return pkt

	###################################################### INITIALIZATION STEPS
	
	def writeIdSzReq(self):
		return self.write(IDSZ_REQ)

	def readIdSzRes(self):
		head = self.readHeader();
		if head[0] != 20:
			raise ProtocolError('expected size of an idsize response')
		if head[2] != 0x80:
			raise ProtocolError('expected first server message to be a response')
		if head[1] != 1:
			raise ProtocolError('expected first server message to be 1')

		sizes = self.recvbuf.unpack( 'iiiii', self.read(20) )
		self.sizes = sizes
		self.recvbuf.config(*sizes)
		self.xmitbuf.config(*sizes)
		return None

	def readHandshake(self):
		data = self.read(len(HANDSHAKE_MSG))
		if data != HANDSHAKE_MSG:
			raise HandshakeError()
		
	def writeHandshake(self):
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
		if qr == 'q':
			self.qmap[ident] = chan
		elif qr == 'r':
			self.rmap[ident] = chan

	def processRequest(self, ident, code, data):
		'used internally by the processor; must have recv control'
		fn = self.rmap.get(code)
		if not fn: return #TODO
		buf = JdwpBuffer()
		buf.config(*self.sizes)
		buf.prepareUnpack(data)
		fn(ident, buf)
		
	def processResponse(self, ident, code, data):
		'used internally by the processor; must have recv control'		
		chan = self.qmap.pop(ident, None)
		
		if not chan: return
		buf = JdwpBuffer()
		buf.config(*self.sizes)
		buf.prepareUnpack(data)
		chan.put((code, buf))

	def hook(self, code, func):
		'''
		func will be invoked when code requests are received in the process loop;
		you cannot safely issue requests here -- therefore, you should generally
		pass the call to a queue.
		'''
		with self.xmitlock:
			self.bindqueue.put(('r', code, func))
		
	####################################################### TRANSMITTING PACKETS
	
	def acquireIdent(self):
		'used internally by the processor; must have xmit control'
		ident = self.nextId
		self.nextId += 2
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
		try:
			while True:
				self.process()
		except EOF:
			return
	
