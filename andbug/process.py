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
## THIS SOFTWARE IS PROVIDED BY SCOTT DUNLOP "AS IS" AND ANY EXPRESS OR 
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

from threading import Thread

class HandshakeError(Exception):
	def __init__(self):
		Error.__init__(
			self, 'handshake error, received message did not match'
		)

HANDSHAKE_MSG = 'JDWP-Handshake'

class Process(Thread):
	'''
	The JDWP Processor is a thread which abstracts the asynchronous JDWP protocol
	into a more synchronous one.  The thread will listen for packets using the
	supplied read function, and transmit them using the write function.  

	Requests are sent by the processor using the calling thread, with a mutex 
	used to protect the write function from concurrent access.  The requesting
	thread is then blocked waiting on a response from the processor thread.

	The Processor will repeatedly use the read function to receive packets, which
	will be dispatched based on whether they are responses to a previous request,
	or events.  Responses to requests will cause the requesting thread to be
	unblocked, thus simulating a synchronous request.
	'''

	def __init__(self, read, write):
		Thread.__init__(self)
		self.read = read
		self.write = write
		self.initialized = False

	def readHandshake(self):
		data = self.read(len(HANDSHAKE_MSG))
		if data != HANDSHAKE_MSG:
			raise HandshakeError()
		
	def writeHandshake(self):
		return self.write(HANDSHAKE_MSG)

	################################################################# THREAD API
	
	def start(self):
		"performs handshaking and solicits configuration information"
		if not self.initialized:
			self.writeHandshake()
			self.readHandshake()
			#TODO self.writeIdSzReq()
			#TODO self.readIdSzRes()
			self.initialized = True
			Thread.start(self)
		return None

	def run(self):
		print "UNIMPLEMENTED" 
		
		#TODO while True:
		#TODO 	self.processPacket(*self.readPacket())
	
