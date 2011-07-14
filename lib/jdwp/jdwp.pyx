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

cdef extern from "wire.h":
	ctypedef unsigned char uint8_t
	ctypedef unsigned short uint16_t
	ctypedef unsigned int uint32_t
	ctypedef unsigned long long uint64_t
	ctypedef int int32_t
	ctypedef long long int64_t
	ctypedef struct jdwp_buffer:
		uint8_t fSz
		uint8_t mSz
		uint8_t oSz
		uint8_t tSz
		uint8_t sSz
		int ofs, len, cap
		char* data
	char* jdwp_en_errors[]

	int jdwp_config( jdwp_buffer* buf, uint8_t fSz, uint8_t mSz, uint8_t oSz, uint8_t tSz, uint8_t sSz )
	int jdwp_prepare( jdwp_buffer* buf, char* data, int len )
	int jdwp_expand( jdwp_buffer* buf, int len )
	void jdwp_purge( jdwp_buffer* buf )
	int jdwp_pack( jdwp_buffer* buf, char format, uint64_t value )
	int jdwp_unpack( jdwp_buffer* buf, char format, uint64_t* value )
	int jdwp_size( jdwp_buffer* buf, char format )

	int jdwp_pack_u8( jdwp_buffer* buf, uint8_t byte)
	int jdwp_pack_u16( jdwp_buffer* buf, uint16_t word )
	int jdwp_pack_u32( jdwp_buffer* buf, uint32_t quad )
	int jdwp_pack_u64( jdwp_buffer* buf, uint64_t octet )

	int jdwp_unpack_u8( jdwp_buffer* buf, uint8_t* byte)
	int jdwp_unpack_u16( jdwp_buffer* buf, uint16_t* word )
	int jdwp_unpack_u32( jdwp_buffer* buf, uint32_t* quad )
	int jdwp_unpack_u64( jdwp_buffer* buf, uint64_t* octet )

	int jdwp_pack_id( jdwp_buffer* buf, uint64_t id, uint8_t sz )
	int jdwp_pack_object_id( jdwp_buffer* buf, uint64_t id )
	int jdwp_pack_field_id( jdwp_buffer* buf, uint64_t id )
	int jdwp_pack_method_id( jdwp_buffer* buf, uint64_t id )
	int jdwp_pack_type_id( jdwp_buffer* buf, uint64_t id )
	int jdwp_pack_frame_id( jdwp_buffer* buf, uint64_t id )

	int jdwp_unpack_id( jdwp_buffer* buf, uint64_t* id, uint8_t sz )
	int jdwp_unpack_object_id( jdwp_buffer* buf, uint64_t* id )
	int jdwp_unpack_field_id( jdwp_buffer* buf, uint64_t* id )
	int jdwp_unpack_method_id( jdwp_buffer* buf, uint64_t* id )
	int jdwp_unpack_type_id( jdwp_buffer* buf, uint64_t* id )
	int jdwp_unpack_frame_id( jdwp_buffer* buf, uint64_t* id )

	int jdwp_pack_str( jdwp_buffer* buf, uint32_t size, char* data )
	int jdwp_unpack_str( jdwp_buffer* buf, uint32_t *size, char** data )

class JdwpError(Exception):
	def __init__(self, code):
		self.code = code
		self.mesg = jdwp_en_errors[code]

	def __str__(self):
		return "jdwp-error (%s): %s" % (self.code, self.mesg)

cdef einz(int code):
	"jdwp error if not zero"
	if code == 0: return
	raise JdwpError(code)

cdef extern from "Python.h":
	object PyInt_FromLong(long l)
	object PyLong_FromLongLong(long long l)
	object PyString_FromStringAndSize(char *s, Py_ssize_t len)
	char* PyString_AsString(object s)
	Py_ssize_t PyString_Size(object s)
	int PyInt_GetMax()
	object PyList_New(Py_ssize_t sz)
	int PyList_SetItem(object lst, Py_ssize_t index, object item)

cdef class JdwpBuffer:
	cdef jdwp_buffer buf

	def __cinit__(self):
		self.buf.data = NULL;

	def __dealloc__(self):
		jdwp_purge(&self.buf)
		
	def packU8( self, uint8_t byte):
		einz( jdwp_pack_u8(&self.buf, byte) )
	def packU16( self, uint16_t word ):
		einz( jdwp_pack_u16(&self.buf, word) )
	def packU32( self, uint32_t quad ):
		einz( jdwp_pack_u32(&self.buf, quad) )
	def packU64( self, uint64_t octet ):
		einz( jdwp_pack_u64(&self.buf, octet) )
	def packInt(self, int32_t i):
		einz( jdwp_pack_u32(&self.buf, i) )
	def packLong(self, int64_t l):
		einz( jdwp_pack_u64(&self.buf, l) )

	def packObjectId( self, uint64_t id ):
		einz( jdwp_pack_object_id( &self.buf, id ) )
	def packFieldId( self, uint64_t id ):
		einz( jdwp_pack_field_id( &self.buf, id ) )
	def packMethodId( self, uint64_t id ):
		einz( jdwp_pack_method_id( &self.buf, id ) )
	def packTypeId( self, uint64_t id ):
		einz( jdwp_pack_type_id( &self.buf, id ) )
	def packFrameId( self, uint64_t id ):
		einz( jdwp_pack_frame_id( &self.buf, id ) )

	def unpackU8(self):
		cdef uint8_t x
		einz( jdwp_unpack_u8(&self.buf, &x) )
		return x
	def unpackU16(self):
		cdef uint16_t x
		einz( jdwp_unpack_u16(&self.buf, &x) )
		return x
	def unpackU32(self):
		cdef uint32_t x
		einz( jdwp_unpack_u32(&self.buf, &x) )
		return x
	def unpackU64(self):
		cdef uint64_t x
		einz( jdwp_unpack_u64(&self.buf, &x) )
		return x
	def unpackInt(self):
		cdef uint32_t x
		einz( jdwp_unpack_u32(&self.buf, &x) )
		return <int32_t>x
	def unpackFloat(self):
		cdef uint32_t x
		einz( jdwp_unpack_u32(&self.buf, &x) )
		return <float>x
	def unpackDouble(self):
		cdef uint32_t x
		einz( jdwp_unpack_u32(&self.buf, &x) )
		return <double>x

	def unpackLong(self):
		cdef uint64_t x
		einz( jdwp_unpack_u64(&self.buf, &x) )
		return <int64_t>x
	
	def unpackObjectId(self):
		cdef uint64_t x
		einz( jdwp_unpack_object_id(&self.buf, &x) )
		return x
	def unpackMethodId(self):
		cdef uint64_t x
		einz( jdwp_unpack_method_id(&self.buf, &x) )
		return x
	def unpackFrameId(self):
		cdef uint64_t x
		einz( jdwp_unpack_frame_id(&self.buf, &x) )
		return x
	def unpackFieldId(self):
		cdef uint64_t x
		einz( jdwp_unpack_field_id(&self.buf, &x) )
		return x
	def unpackTypeId(self):
		cdef uint64_t x
		einz( jdwp_unpack_type_id(&self.buf, &x) )
		return x

	def unpackStr(self):
		cdef uint32_t sz
		cdef char* str
		einz( jdwp_unpack_str(&self.buf, &sz, &str) )
		return PyString_FromStringAndSize(str, sz)
	
	def packStr(self, str):
		cdef char* cstr
		cdef Py_ssize_t sz
		cstr = PyString_AsString(str)
		sz = PyString_Size(str)
		einz( jdwp_pack_str(&self.buf, sz, cstr) )

				
	def config(self, fSz = None, mSz = None, oSz = None, tSz = None, sSz = None):
		if fSz is not None: self.buf.fSz = fSz
		if mSz is not None: self.buf.mSz = mSz
		if oSz is not None: self.buf.oSz = oSz
		if tSz is not None: self.buf.tSz = tSz
		if sSz is not None: self.buf.sSz = sSz

	cdef size(self, fmt, args):
		cdef int i
		cdef int sz
		cdef char op
		cdef char* cfmt
		cfmt = fmt

		sz = 0

		for 0 <= i < len(fmt):
			val = args[i]
			op = cfmt[i]
			if op == c'$':
				sz += 4 + len(val)
			else:
				inc = jdwp_size(&self.buf, op)
				if inc == 0: 
					raise JdwpError(2)
				sz += inc

		return sz

	def data(self):
		cdef char* str
		cdef Py_ssize_t len

		str = self.buf.data
		if str == NULL: 
			return ''
		str = str + self.buf.ofs
		len = self.buf.len
		return PyString_FromStringAndSize(str, len)

	def preparePack(self, sz = 1024):
		jdwp_prepare(&self.buf, NULL, sz)	

	def prepareUnpack(self, str):
		cdef char* cstr
		cdef Py_ssize_t sz

		cstr = PyString_AsString(str)
		sz = PyString_Size(str)
		jdwp_prepare(&self.buf, cstr, sz)				

	def pack(self, fmt, *args):
		cdef char* cfmt
		cdef uint64_t val
		cdef int i
		cdef char op

		cfmt = PyString_AsString(fmt)
		sz = self.size(cfmt, args)
		self.preparePack(sz)
		for 0 <= i < len(fmt):
			op = cfmt[i]
			if op == c'$':
				self.packStr(args[i])
			else:
				val = args[i]
				jdwp_pack( &self.buf, op, val ) #TODO: dispatch on op
			#TODO: HANDLE-ERROR
		return PyString_FromStringAndSize(self.buf.data, sz)
	
	def ipack(self, fmt, *args):
		cdef char* cfmt
		cdef uint64_t val
		cdef int i
		cdef char op

		cfmt = PyString_AsString(fmt)
		sz = self.size(cfmt, args)
		jdwp_expand(&self.buf, sz)
		for 0 <= i < len(fmt):
			op = cfmt[i]
			if op == c'$':
				self.packStr(args[i])
			else:
				val = args[i]
				jdwp_pack( &self.buf, op, val ) #TODO: dispatch on op
			#TODO: HANDLE-ERROR
		return PyString_FromStringAndSize(self.buf.data, sz)
	
	def unpack(self, fmt, data = None):
		cdef char* cfmt
		cdef uint64_t v64
		cdef uint32_t v32
		cdef int imax
		cdef int i
		cdef char op
		cdef object val

		if data is not None:
			self.prepareUnpack(data)

		cfmt = PyString_AsString(fmt)
		vals = [None,] * len(fmt)
		imax = PyInt_GetMax()

		for 0 <= i < len(fmt):
			v64 = 0
			op = cfmt[i]
			if op == c'$':
				val = self.unpackStr()
			else:
				jdwp_unpack(&self.buf, cfmt[i], &v64) #TODO: dispatch on op		
				
				if v64 > imax:
					val = PyLong_FromLongLong(v64)
				elif v64 < -imax:
					val = PyLong_FromLongLong(v64)
				else:
					val = PyInt_FromLong(v64)
				
			vals[i] = val

		return vals

	# def pack(self, fmt, *args):
	# 	cdef char* cfmt
	# 	cdef uint64_t val
	# 	cdef int i

	# 	cfmt = PyString_AsString(fmt)
	# 	sz = jdwp_size(&self.buf, cfmt)
	# 	#TODO: HANDLE-ERROR
	# 	jdwp_prepare(&self.buf, NULL, sz)
	# 	#TODO: HANDLE-ERROR
	# 	for 0 <= i < len(fmt):
	# 		val = args[i]
	# 		jdwp_pack( &self.buf, cfmt[i], val )
	# 		#TODO: HANDLE-ERROR
	# 	return PyString_FromStringAndSize(self.buf.data, sz)

	# def unpack(self, fmt, data):
	# 	cdef char* cfmt
	# 	cdef uint64_t v64
	# 	cdef uint32_t v32
	# 	cdef int imax
	# 	cdef int i

	# 	cfmt = PyString_AsString(fmt)
	# 	vals = [None,] * len(fmt)
	# 	imax = PyInt_GetMax()

	# 	for 0 <= i < len(fmt):
	# 		v64 = 0
	# 		jdwp_unpack(&self.buf, cfmt[i], &v64)			
	# 		if v64 > imax:
	# 			vals[i] = PyLong_FromLongLong(v64)
	# 		elif v64 < -imax:
	# 			vals[i] = PyLong_FromLongLong(v64)
	# 		else:
	# 			vals[i] = PyInt_FromLong(v64)

	# 	return vals


'''
PROBLEMS:
  - using a uint64_t for everything in and out of a pack or unpack causes problems
    - hard to know whether a return value is a 8, 16, 32 or 64-bit integer
    - expose individual unpack funcs, lifting them to cdef'd methods, and make unpack use that

'''
