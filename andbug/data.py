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

class pool(object):
	'''
	a pool of singleton objects such that, for any combination of constructor 
	and 1 or more initializers, there may be zero or one objects; attempting
	to reference a nonexisted object causes it to be created.

	example:
		def t(a): return [a,0]
		p = pool()
		t1 = p(t,1)
		t2 = p(t,2)
		p(t,1)[1] = -1
		# t1[1] is now -1, not 1
	'''
	def __init__(self):
		self.pools = {}
	def __call__(self, *ident):
		pool = self.pools.get(ident)
		if pool is None:
			pool = ident[0](self, *ident[1:])
			self.pools[ident] = pool
		return pool

class item(object):
	'''
	an item which supports the defer property defined below
	'''
	def __init__(self, pool):
		self.pool = pool
		self.props = {}

class view(object):
	'''
	a homogenous collection of objects that may be acted upon in unison, such
	that calling a method on the collection with given arguments would result
	in calling that method on each object and returning the results as a list
	'''
	def __init__(self, items):
		self.items = items
	def __repr__(self):
		return '(' + ', '.join(str(item) for item in self.items) + ')'
	def __len__(self):
		return len(self.items)
	def __getitem__(self, index):
		return self.items[index]
	def __iter__(self):
		return self.items.__iter__()
	def __getattr__(self, key):
		def poolcall(*args, **kwargs):
			return view( 
				getattr(item, key)(*args, **kwargs) for item in self.items
			)
		poolcall.func_name = '*' + key
		return poolcall
	def get(self, key):
		return view(getattr(item, key) for item in self.items)
	def set(self, key, val):
		for item in self.items:
			setattr(item, key, val)

class defer(object):
	'''
	a property decorator that, when applied, specifies a property that relies
	on the execution of a costly function for its resolution; this permits the
	deferral of evaluation until the first time it is needed.

	unlike other deferral implementation, this one accepts the reality that the
	product of a single calculation may be multiple properties
	'''
	def __init__(self, func, name):
		self.func = func
		self.name = name
	def __get__(self, obj, type=None):
		try:
			val = obj.props[self.name]
		except KeyError:
			f = self.func
			f(obj)
			val = obj.props[self.name]
		return val
	def __set__(self, obj, value):
		obj.props[self.name] = value
	
if __name__ == '__main__':
	class classitem(item):
		def __init__(self, pool, cid):
			item.__init__(self, pool)
			self.cid = cid
		def __repr__(self):
			return '<class %s>' % self.cid

	class methoditem(item):
		def __init__(self, pool, cid, mid):
			item.__init__(self, pool)
			self.cid = cid
			self.mid = mid
		def __repr__(self):
			return '<method %s:%s>' % (self.cid, self.mid)
		def classitem(self):
			return self.pool(classitem, self.cid)
		def load_line_table(self):
			print "LOAD-LINE-TABLE", self.cid, self.mid
			self.first = 1
			self.last = 1
			self.lines = []
		def trace(self):
			print "TRACE", self.cid, self.mid

		first = defer(load_line_table, 'first')
		last =  defer(load_line_table, 'last')
		lines = defer(load_line_table, 'lines')


	pool = pool()
	m1 = pool(methoditem, 'c1', 'm1')
	m2 = pool(methoditem, 'c1', 'm2')
	m3 = pool(methoditem, 'c2', 'm3')
	v = view((m1,m2,m3))
	print v
	print v.trace
	print v.trace()
	print (v.get('first'))
	print (v.get('last'))
	print v.classitem()
	print list(m for m in v)

