/* Copyright 2011, IOActive All rights reserved.

   AndBug is free software: you can redistribute it and/or modify it under 
   the terms of version 3 of the GNU Lesser General Public License as 
   published by the Free Software Foundation.

   AndBug is distributed in the hope that it will be useful, but WITHOUT ANY
   WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS 
   FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for 
   more details.

   You should have received a copy of the GNU Lesser General Public License
   along with AndBug.  If not, see <http://www.gnu.org/licenses/>. 
*/

#ifndef JDWPBUF_H 
#define JDWPBUF_H 1

/* OVERVIEW:
   The Java Debugging Wire Protocol has several annoying habits, including a 
   fully asynchronous messaging protocol, variably sized fields, and a case
   of committee-itis.  Py-JDWP uses a simple C library to pack and unpack
   primitives, including integers of various sizes, and variably sized
   identifiers.  The remaining insanity is left to python modules that rely 
   on jdwp_wire.
*/

/* IMPLEMENTATION:
   - Functions in this library that return int are, in fact, returning error codes or 0 for success.
   - Error messages can be found by taking the error code and looking up the entry in jdwp_en_errors.
*/

#include <stdint.h>
#include <stdarg.h>

#define JDWP_SZ_UNSUPPORTED 1
#define JDWP_OP_UNSUPPORTED 2
#define JDWP_NEED_CAP 3
#define JDWP_NEED_LEN 4
#define JDWP_HEAP_FAULT 5
#define JDWP_EOF 6
#define JDWP_HANDSHAKE_ERROR 7
#define JDWP_FAIL 8

extern char* jdwp_en_errors[];

/** represents an active JDWP buffer and associated state */
typedef struct {
	uint8_t fSz;
	uint8_t mSz;
	uint8_t oSz;
	uint8_t tSz;
	uint8_t sSz;
	int ofs, len, cap;
	char* data;
} jdwp_buffer;

/** creates a new buffer, backed by a copy of len bytes from data, which may be NULL */
int jdwp_prepare( jdwp_buffer* buf, char* data, int len );

/** purges the associated heap memory from a jdwp_buffer */
void jdwp_purge( jdwp_buffer* buf );

/** packs a 8 bit ordinal into the buffer */
int jdwp_pack_u8( jdwp_buffer* buf, uint8_t byte);

/** packs a 16 bit ordinal into the buffer */
int jdwp_pack_u16( jdwp_buffer* buf, uint16_t word );

/** packs a 32 bit ordinal into the buffer */
int jdwp_pack_u32( jdwp_buffer* buf, uint32_t quad );

/** packs a 64 bit ordinal into the buffer */
int jdwp_pack_u64( jdwp_buffer* buf, uint64_t octet );

/** unpacks a 8 bit ordinal from the buffer */
int jdwp_unpack_u8( jdwp_buffer* buf, uint8_t* byte);

/** unpacks a 16 bit ordinal from the buffer */
int jdwp_unpack_u16( jdwp_buffer* buf, uint16_t* word );

/** unpacks a 32 bit ordinal from the buffer */
int jdwp_unpack_u32( jdwp_buffer* buf, uint32_t* quad );

/** unpacks a 64 bit ordinal from the buffer */
int jdwp_unpack_u64( jdwp_buffer* buf, uint64_t* octet );

/** packs an identifier into the buffer; sz is the number of bytes to be used */
int jdwp_pack_id( jdwp_buffer* buf, uint64_t id, uint8_t sz );

/** unpacks an identifier from the buffer; sz is the number of bytes to be used */
int jdwp_unpack_id( jdwp_buffer* buf, uint64_t* id, uint8_t sz );

/** packs an object id into the buffer */
int jdwp_pack_object_id( jdwp_buffer* buf, uint64_t id );

/** packs a field id into the buffer */
int jdwp_pack_field_id( jdwp_buffer* buf, uint64_t id );

/** packs a method id into the buffer */
int jdwp_pack_method_id( jdwp_buffer* buf, uint64_t id );

/** packs a type id into the buffer */
int jdwp_pack_type_id( jdwp_buffer* buf, uint64_t id );

/** packs a stack (frame) id into the buffer */
int jdwp_pack_frame_id( jdwp_buffer* buf, uint64_t id );

/** packs a string into the buffer */
int jdwp_pack_str( jdwp_buffer* buf, uint32_t size, char* data );

/** unpacks an object id from the buffer */
int jdwp_unpack_object_id( jdwp_buffer* buf, uint64_t* id );

/** unpacks a field id from the buffer */
int jdwp_unpack_field_id( jdwp_buffer* buf, uint64_t* id );

/** unpacks a method id from the buffer */
int jdwp_unpack_method_id( jdwp_buffer* buf, uint64_t* id );

/** unpacks a type id from the buffer */
int jdwp_unpack_type_id( jdwp_buffer* buf, uint64_t* id );

/** unpacks a frame id from the buffer */
int jdwp_unpack_frame_id( jdwp_buffer* buf, uint64_t* id );

/** unpacks a string from the buffer */
int jdwp_unpack_str( jdwp_buffer* buf, uint32_t *size, char** data );

/** packs fields into the current buf, writing field by field, and returning when complete */
int jdwp_pack( jdwp_buffer* buf, char format, uint64_t value );

/** unpacks fields from the current buf, reading field by field, and returning when complete */
int jdwp_unpack( jdwp_buffer* buf, char format, uint64_t* value );

/** packs fields into the current buf, writing field by field, and returning when complete */
int jdwp_packf( jdwp_buffer* buf, char* format, ... );

/** unpacks fields from the current buf, reading field by field, and returning when complete */
int jdwp_unpackf( jdwp_buffer* buf, char* format, ... );

/** packs fields into the current buf, writing field by field, and returning when complete */
int jdwp_packfv( jdwp_buffer* buf, char* format, va_list ap );

/** unpacks fields from the current buf, reading field by field, and returning when complete */
int jdwp_unpackfv( jdwp_buffer* buf, char* format, va_list ap );

/** returns the size that a format would produce. */
int jdwp_size( jdwp_buffer* buf, const char format );

/* PACK FORMAT STRINGS:
	1 -- unsigned 1-byte ordinal
	2 -- unsigned 2-byte ordinal
	4 -- unsigned 4-byte ordinal
	8 -- unsigned 8-byte ordinal
	i -- signed 4-byte ordingal
	l -- signed 8-byte ordinal
	o -- object id, size config dependent
	t -- type id, size config dependent
	f -- field id, size config dependent
	s -- stack id, size config dependent
	m -- method id, size config dependent
	$ -- string, size length dependent
*/

#endif
