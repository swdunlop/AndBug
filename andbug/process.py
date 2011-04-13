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

import andbug, sqlite3

def seq(*items): return items

DB_SCHEMA = (
	# CLASSES
	'create table if not exists classes('
	'    tag,'
	'    id PRIMARY KEY,'
	'    jni,'
	'    gen,'
	'    status'
	');'

	# CLASSES BY JNI INDEX
	'create index if not exists i_classes_jni on classes(jni);'

	# METHODS
	'create table if not exists methods('
	'    class,'
	'    id,'# PRIMARY KEY,'
	'    name,'
	'    jni,'
	'    gen,'
	'    mods'
	');'

	# METHODS BY JNI INDEX
	'create index if not exists i_methods_jni on methods(jni);'
);

DB_INSERT_CLASS = 'insert into classes values(?, ?, ?, ?, ?);'

class Failure(Exception):
	def __init__(self, code):
		Exception.__init__(self, 'request failed, code %s', code)

class Process(object):
	def __init__(self, conn = None, dbpath=':memory:'):
		self.conn = None
		self.portno = None
		self.db = sqlite3.connect(dbpath)
		self.db.text_factory = str
		self.db.executescript(DB_SCHEMA)
		self.cache = {}

	def is_cached(self, key):
		return self.cache.get(key)
	
	def set_cached(self, key):
		self.cache[key] = True
	
	def connect(self, portno = None):
		if portno: 
			self.portno = portno
		if self.conn is None: 
			self.conn = andbug.proto.connect('127.0.0.1', self.portno)
		return self.conn

	def load_classes(self):
		if self.is_cached('c'):
			return 

		code, buf = self.connect().request(0x0114)
		if code != 0:
			raise Failure(code)
				
		def unpack_entries():
			ct = buf.unpackU32()
			for i in range(0, ct):
				yield buf.unpack('1t$$i')

		cur = self.db.cursor()
		cur.execute('delete from classes;')
		cur.executemany(
			'insert into classes values(?, ?, ?, ?, ?);',
			unpack_entries()
		)
	
		self.set_cached('c')

	def load_methods(self, cid):
		if self.is_cached('m:' + str(cid)):
			return 

		conn = self.connect()
		buf = conn.buffer()
		buf.pack("t", cid)
		code, buf = conn.request(0x020F, buf.data())
		if code != 0:
			raise Failure(code)
				
		def unpack_entries():
			ct = buf.unpackU32()
			for i in range(0, ct):
				yield seq(cid, *buf.unpack('m$$$i'))
		
		cur = self.db.cursor()
		cur.execute(
			'delete from methods where class = ?', (cid,)
		)
		cur.executemany(
			'insert into methods values(?, ?, ?, ?, ?, ?);',
			unpack_entries()
		)
		self.set_cached('m:' + str(cid))

	def classes(self, jni=None):
		self.load_classes()
		cur = self.db.cursor()
		if jni:
			cur.execute(
				'select * from classes where jni = ?', (jni,)
			)
		else:
			cur.execute('select * from classes;')

		return class_list(self, (class_record(*row) for row in cur.fetchall()))

from collections import namedtuple

class_record = namedtuple('class_record', (
	'tag', 'cid', 'jni', 'gen', 'status'
))
method_record = namedtuple('method_record', (
	'cid', 'mid', 'name', 'jni', 'gen', 'mods'
))

class class_list(tuple):
	def __new__(self, proc, items):
		self.proc = proc
		return tuple.__new__(self, items)

	def methods(self, name=None, jni=None):
		def generator():
			for row in self:
				cid = row.cid
				self.proc.load_methods(cid)
				cur = self.proc.db.cursor()
				if name and jni:
					cur.execute(
						'select * from methods where class = ? and name = ? and jni = ?;',
						(cid, name, jni)
					)
				elif name:
					cur.execute(
						'select * from methods where class = ? and name = ?;',
						(cid, name)
					)
				elif jni:
					cur.execute(
						'select * from methods where class = ? and jni = ?;', (cid,jni)
					)
				else:
					cur.execute(
						'select * from methods where class = ?;', (cid,)
					)
				for row in cur.fetchall():
					yield row

		return method_list(self.proc, (method_record(*row) for row in generator()))

class method_list(tuple):
	def __new__(self, proc, items):
		self.proc = proc
		return tuple.__new__(self, items)
