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

import andbug, andbug.data
from andbug.data import defer

class Failure(Exception):
	def __init__(self, code):
		Exception.__init__(self, 'request failed, code %s', code)

class Location(object):
	def __init__(self, proc, cid, mid, loc):
		self.proc = proc
		self.cid = cid
		self.mid = mid
		self.loc = loc
		self.line = None

	def __str__(self):
		return '<loc 0x%x in class %r, method %r>' % (
			self.loc, self.klass.name, self.method.name
		)

	@property
	def method(self):
		return self.proc.pool(Method, self.proc, self.cid, self.mid)
	
	@property
	def klass(self):
		return self.proc.pool(Class, self.proc, self.cid)

	def packTo(self, buf):
		c = self.klass
		buf.ipack('1tm8', c.tag, self.cid, self.mid, self.loc)

	@classmethod
	def unpackFrom(impl, proc, buf):
		tag, cid, mid, loc = buf.unpack('1tm8')
		return impl(proc, cid, mid, loc)

class Method(object):
	def __init__(self, proc, cid, mid):
		self.proc = proc
		self.cid = cid
		self.mid = mid

	@property
	def klass(self):
		return self.proc.pool(Class, self.proc, self.cid)

	def __str__(self):
		return '%s.%s%s' % (
			self.klass, self.name, self.jni 
	)		
	
	def __repr__(self):
		return '<method %s>' % self

	def load_table(self):
		proc = self.proc
		conn = proc.conn
		pool = proc.pool
		cid = self.cid
		mid = self.mid
		data = conn.buffer().pack('tm', cid, mid)
		code, buf = conn.request(0x0601, data)
		if code != 0: raise Failure(code)
		
		f, l, ct = buf.unpack('88i')
		if (f == -1) or (l == -1): 
			self.firstLoc = None
			self.lastLoc = None
			self.lineTable = andbug.data.view([])
			#TODO: How do we handle native methods?
 
		self.firstLoc = pool(Location, proc, cid, mid, f)
		self.lastLoc = pool(Location, proc, cid, mid, l)

		ll = {}
		self.lineLocs = ll
		def line_loc():
			loc, line  = buf.unpack('8i')
			loc = pool(Location, proc, cid, mid, loc)
			loc.line = line
			ll[line] = loc

		for i in range(0,ct):
			line_loc()
	
	firstLoc = defer(load_table, 'firstLoc')
	lastLoc = defer(load_table, 'lastLoc')
	lineTable = defer(load_table, 'lineTable')

class Class(object): 
	def __init__(self, proc, cid):
		self.proc = proc
		self.cid = cid
	
	def __str__(self):
		return self.name
	
	def __repr__(self):
		return '<class %s>' % self

	def load_methods(self):
		cid = self.cid
		proc = self.proc
		conn = proc.conn
		pool = proc.pool
		buf = conn.buffer()
		buf.pack("t", cid)
		code, buf = conn.request(0x020F, buf.data())
		if code != 0:
			raise Failure(code)

		ct = buf.unpackU32()
				
		def load_method():
			mid, name, jni, gen, flags = buf.unpack('m$$$i')
			obj = pool(Method, proc, cid, mid)
			obj.name = name
			obj.jni = jni
			obj.gen = gen
			obj.flags = flags
			return obj

		self.methodList = andbug.data.view(load_method() for i in range(0, ct))
		self.methodByJni = andbug.data.multidict()
		self.methodByName = andbug.data.multidict()

		for item in self.methodList:
			jni = item.jni
			name = item.name
			self.methodByJni[jni] = item
			self.methodByName[name] = item
	
	methodList = defer(load_methods, 'methodList')
	methodByJni = defer(load_methods, 'methodByJni')
	methodByName = defer(load_methods, 'methodByName')

	methodList = defer(load_methods, 'methodList')
	methodByJni = defer(load_methods, 'methodByJni')
	methodByName = defer(load_methods, 'methodByName')

	def methods(self, name=None, jni=None):
		if name and jni:
			seq = self.methodByName[name]
			seq = filter(x in seq, self.methodByJni[jni])
		elif name:
			seq = andbug.data.view(self.methodByName[name])
		elif jni:
			seq = self.methodByJni[jni]
		else:
			seq = self.methodList
		return andbug.data.view(seq)
	
	@property
	def name(self):
		name = self.jni
		if name.startswith('L'): name = name[1:]
		if name.endswith(';'): name = name[:-1]
		name = name.replace('/', '.')
		return name

class Process(object):
	def __init__(self, portno = None, conn = None):
		self.pool = andbug.data.pool()
		self.conn = conn
		if conn is None:
			self.connect(portno)

	def connect(self, portno = None):
		if portno: 
			self.portno = portno
			if self.conn is None: 
				self.conn = andbug.proto.connect('127.0.0.1', self.portno)
		return self.conn

	def load_classes(self):
		code, buf = self.connect().request(0x0114)
		if code != 0:
			raise Failure(code)

		def load_class():
			tag, cid, jni, gen, flags = buf.unpack('1t$$i')
			obj = self.pool(Class, self, cid)
			obj.tag = tag
			obj.cid = cid
			obj.jni = jni
			obj.gen = gen
			obj.flags = flags
			return obj 
						
		ct = buf.unpackU32()

		self.classList = andbug.data.view(load_class() for i in range(0, ct))
		self.classByJni = andbug.data.multidict()
		for item in self.classList:
			self.classByJni[item.jni] = item

	classList = defer(load_classes, 'classList')
	classByJni = defer(load_classes, 'classByJni')

	def classes(self, jni=None):
		if jni:
			seq = self.classByJni[jni]
		else:
			seq = self.classList
		return andbug.data.view(seq)
	
