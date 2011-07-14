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
   
#include "wire.h"
#include <string.h>
#include <stdlib.h>
#include <arpa/inet.h>
#include <stdarg.h>

// Thank you, POSIX, for your shortsightedness, Linux for your haste, and BSD
// for being as bad as Linux.  Can a brother get a standards update around 
// here? Until then.. 

#if defined(__linux__) 
#  include <endian.h>
#  define htonll htobe64
#  define ntohll be64toh
#elif defined(__FreeBSD__) || defined(___NetBSD__) || defined(ANDROID)
#  include <sys/endian.h>
#  define htonll htobe64
#  define ntohll betoh64
#elif defined(___OpenBSD__)
#  include <sys/types.h>
#  define htonll htobe64
#  define ntohll be64toh
#elif defined(__DARWIN_OSSwapInt64)
#  define htonll(x) __DARWIN_OSSwapInt64(x)
#  define ntohll(x) __DARWIN_OSSwapInt64(x)
#else
#  error "must define htonll/ntohll for this platform"
#endif

char *jdwp_en_errors[] = {
	NULL,
	"java debug wire protocol identifier size not supported",
	"jdwp packing operand character not supported",
	"insufficient jdwp capacity to pack value",
	"insufficient jdwp length to unpack value",
	"insufficient heap memory to store data",
	"transport closed or end of file reached",
	"could not complete handshake with process",
        "a jdwp failure was received"
};

#define REQUIRE_CAP(n) if (jdwp_expand(buf, (n))) return JDWP_HEAP_FAULT;
#define REQUIRE_LEN(n) if ((buf->len - buf->ofs) < n) return JDWP_NEED_LEN;

int jdwp_expand( jdwp_buffer* buf, int req ){
	int cap = buf->cap;
	req += buf->len;
	if (req < cap) return 0; // we'll be fine.
	if (cap < 256) cap = 256; // jumps up to 256 bytes to reduce flutter
again:
	cap <<= 2;
	if (cap < req) goto again;

	char* data = realloc(buf->data, cap);
	if (data == NULL) return JDWP_HEAP_FAULT;
	buf->cap = cap;
	buf->data = data;
	return 0;
}

int jdwp_pack_str( jdwp_buffer* buf, uint32_t size, char* data ){
	REQUIRE_CAP(size + 4);
	jdwp_pack_u32(buf, size);
	memcpy(buf->data + buf->len, data, size);
	buf->len += size;
    return 0;
}

int jdwp_pack_u8( jdwp_buffer* buf, uint8_t byte){
	REQUIRE_CAP(1);
	*(uint8_t*)(buf->data + buf->len) = byte;
	buf->len += 1;
	return 0;
}
int jdwp_pack_u16( jdwp_buffer* buf, uint16_t word ){
	REQUIRE_CAP(2);
	*(uint16_t*)(buf->data + buf->len) = htons(word);
	buf->len += 2;
	return 0;
}
int jdwp_pack_u32( jdwp_buffer* buf, uint32_t quad ){
	REQUIRE_CAP(4);
	*(uint32_t*)(buf->data + buf->len) = htonl(quad);
	buf->len += 4;
	return 0;
}
int jdwp_pack_u64( jdwp_buffer* buf, uint64_t octet ){
	REQUIRE_CAP(8);
	*(uint64_t*)(buf->data + buf->len) = htonll(octet);
	buf->len += 8;
	return 0;
}
int jdwp_unpack_u8( jdwp_buffer* buf, uint8_t* byte){
	REQUIRE_LEN(1);
	*byte = *(uint8_t*)(buf->data + buf->ofs);
	buf->ofs += 1;
	return 0;
}
int jdwp_unpack_u16( jdwp_buffer* buf, uint16_t* word ){
	REQUIRE_LEN(2);
	*word = ntohs(*(uint16_t*)(buf->data + buf->ofs));
	buf->ofs += 2;
	return 0;
}
int jdwp_unpack_u32( jdwp_buffer* buf, uint32_t* quad ){
	REQUIRE_LEN(4);
	*quad = ntohl(*(uint32_t*)(buf->data + buf->ofs));
	buf->ofs += 4;
	return 0;
}
int jdwp_unpack_u64( jdwp_buffer* buf, uint64_t* octet ){
	REQUIRE_LEN(8);
	*octet = ntohll(*(uint64_t*)(buf->data + buf->ofs));
	buf->ofs += 8;
	return 0;
}
int jdwp_unpack_str( jdwp_buffer* buf, uint32_t *size, char** data ){
    uint32_t sz;
    int err = jdwp_unpack_u32(buf, &sz);
    if (err) return err;
    REQUIRE_LEN(sz);
    *size = sz;
    *data = buf->data + buf->ofs;
    buf->ofs += sz;
    return 0;
}

int jdwp_pack_id( jdwp_buffer* buf, uint64_t id, uint8_t sz ){
	switch (sz){
	case 1:
		return jdwp_pack_u8(buf, (uint8_t)id);
	case 2:
		return jdwp_pack_u16(buf, (uint16_t)id);
	case 4:
		return jdwp_pack_u32(buf, (uint32_t)id);
	case 8:
		return jdwp_pack_u64(buf, id);
	default:
		return JDWP_SZ_UNSUPPORTED;
	}
}

int jdwp_unpack_id( jdwp_buffer* buf, uint64_t* id, uint8_t sz ){
	*id = 0; // forces all bytes to be zero..
	switch (sz){
	case 1:
		return jdwp_unpack_u8(buf, (uint8_t*)id);
	case 2:
		return jdwp_unpack_u16(buf, (uint16_t*)id);
	case 4:
		return jdwp_unpack_u32(buf, (uint32_t*)id);
	case 8:
		return jdwp_unpack_u64(buf, id);
	default:
		return JDWP_SZ_UNSUPPORTED;
	}
}

int jdwp_prepare( jdwp_buffer* buf, char* data, int len ){
	if (buf->data == NULL){
		buf->data = malloc(len);
	}else if (len > buf->cap){
		buf->data = realloc(buf->data, len);
	}; // we do not collapse the heap, ever.. call it a character flaw.
	if (buf->data == NULL) return JDWP_HEAP_FAULT;
	if (data == NULL){
		buf->len = 0;
		// we also don't zeroize memory; also a character flaw.
	}else{
		memcpy(buf->data, data, len);
		buf->len = len;
	}
	buf->cap = len;
	buf->ofs = 0;
	return 0;
}

void jdwp_purge( jdwp_buffer* buf ){
	if (buf->data == NULL) return;
	free(buf->data);
	buf->data = NULL;
}

int jdwp_pack( jdwp_buffer* buf, char format, uint64_t value ){
	switch (format) {
	case '1':
		return jdwp_pack_u8(buf, (uint8_t)value);
	case '2':
		return jdwp_pack_u16(buf, (uint16_t)value);
	case '4':
		return jdwp_pack_u32(buf, (uint32_t)value);
	case '8':
		return jdwp_pack_u64(buf, value);
	case 'i':
		return jdwp_pack_u32(buf, (uint32_t)value);
	case 'l':
		return jdwp_pack_u64(buf, value);
	case 'o':
		return jdwp_pack_id(buf, value, buf->oSz);
	case 't':
		return jdwp_pack_id(buf, value, buf->tSz);
	case 'f':
		return jdwp_pack_id(buf, value, buf->fSz);
	case 's':
		return jdwp_pack_id(buf, value, buf->sSz);
	case 'm':
		return jdwp_pack_id(buf, value, buf->mSz);
	default:
		return JDWP_OP_UNSUPPORTED;
	}
}

int jdwp_unpack( jdwp_buffer* buf, char format, uint64_t *value ){	
	switch (format) {
	case '1':
		return jdwp_unpack_u8(buf, (uint8_t*)value);
	case '2':
		return jdwp_unpack_u16(buf, (uint16_t*)value);
	case '4':
		return jdwp_unpack_u32(buf, (uint32_t*)value);
	case '8':
		return jdwp_unpack_u64(buf, value);
	case 'i':
		return jdwp_unpack_u32(buf, (uint32_t*)value);
	case 'l':
		return jdwp_unpack_u64(buf, value);
	case 'o':
		return jdwp_unpack_id(buf, value, buf->oSz);
	case 't':
		return jdwp_unpack_id(buf, value, buf->tSz);
	case 'f':
		return jdwp_unpack_id(buf, value, buf->fSz);
	case 's':
		return jdwp_unpack_id(buf, value, buf->sSz);
	case 'm':
		return jdwp_unpack_id(buf, value, buf->mSz);
	default:
		return JDWP_OP_UNSUPPORTED;
	}
}

int jdwp_size( jdwp_buffer* buf, char format ){	
	switch (format) {
	case 0:
		return 0;
	case '1':
		return 1;
	case '2':
		return 2;
	case 'i':
	case '4':
		return 4;
	case 'l':
	case '8':
		return 8;
	case 'o':
		return buf->oSz;
	case 't':
		return buf->tSz;
	case 'f':
		return buf->fSz;
	case 's':
		return buf->sSz;
	case 'm':
		return buf->mSz;
	default:
		return 0;
	}
}

int jdwp_pack_object_id( jdwp_buffer* buf, uint64_t id ){
	return jdwp_pack_id( buf, id, buf->oSz );
}
int jdwp_pack_field_id( jdwp_buffer* buf, uint64_t id ){
	return jdwp_pack_id( buf, id, buf->fSz );
}
int jdwp_pack_method_id( jdwp_buffer* buf, uint64_t id ){
	return jdwp_pack_id( buf, id, buf->mSz );
}
int jdwp_pack_type_id( jdwp_buffer* buf, uint64_t id ){
	return jdwp_pack_id( buf, id, buf->tSz );
}
int jdwp_pack_frame_id( jdwp_buffer* buf, uint64_t id ){
	return jdwp_pack_id( buf, id, buf->sSz );
}
int jdwp_unpack_object_id( jdwp_buffer* buf, uint64_t* id ){
	return jdwp_unpack_id( buf, id, buf->oSz );
}
int jdwp_unpack_field_id( jdwp_buffer* buf, uint64_t* id ){
	return jdwp_unpack_id( buf, id, buf->fSz );
}
int jdwp_unpack_method_id( jdwp_buffer* buf, uint64_t* id ){
	return jdwp_unpack_id( buf, id, buf->mSz ); 
}
int jdwp_unpack_type_id( jdwp_buffer* buf, uint64_t* id ){
	return jdwp_unpack_id( buf, id, buf->tSz );
}
int jdwp_unpack_frame_id( jdwp_buffer* buf, uint64_t* id ){
	return jdwp_unpack_id( buf, id, buf->sSz );
}

/** packs fields into the current buf, writing field by field, and returning when complete */
int jdwp_packf( jdwp_buffer* buf, char* format, ... ){
	va_list ap;
	va_start(ap, format);
	int err = jdwp_packfv(buf, format, ap);
	va_end(ap);
	return err;
}

int jdwp_packfv( jdwp_buffer* buf, char* format, va_list ap ){
	uint32_t v32;
	uint64_t v64;
	int err = 0;

	while(*format) {
		switch(*format++) {
		case '1':
			v32 = va_arg(ap, uint32_t);
			err = jdwp_pack_u8(buf, v32);
			break;
		case '2':
			v32 = va_arg(ap, uint32_t);
			err = jdwp_pack_u16(buf, v32);
			break;
		case '4':
			v32 = va_arg(ap, uint32_t);
			err = jdwp_pack_u32(buf, v32);
			break;
		case '8':
			v64 = va_arg(ap, uint64_t);
			err = jdwp_pack_u64(buf, v64);
			break;
		case 'i':
			v32 = va_arg(ap, uint32_t);
			err = jdwp_pack_u32(buf, v32);
			break;
		case 'l':
			v64 = va_arg(ap, uint64_t);
			err = jdwp_pack_u64(buf, v64);
			break;
		case 'o':
			v64 = va_arg(ap, uint64_t);
			err = jdwp_pack_id(buf, v64, buf->oSz);
			break;
		case 't':
			v64 = va_arg(ap, uint64_t);
			err = jdwp_pack_id(buf, v64, buf->tSz);
			break;
		case 'f':
			v64 = va_arg(ap, uint64_t);
			err = jdwp_pack_id(buf, v64, buf->fSz);
			break;
		case 's':
			v64 = va_arg(ap, uint64_t);
			err = jdwp_pack_id(buf, v64, buf->sSz);
			break;
		case 'm':
			v64 = va_arg(ap, uint64_t);
			err = jdwp_pack_id(buf, v64, buf->mSz);
			break;
		default:
			err = JDWP_OP_UNSUPPORTED;
		}
		if (err) break;
	};
	return err;
}

/** unpacks fields from the current buf, reading field by field, and returning when complete */
int jdwp_unpackf( jdwp_buffer* buf, char* format, ... ){
	va_list ap;
	va_start(ap, format);
	int err = jdwp_unpackfv(buf, format, ap);
	va_end(ap);
	return err;
}

/** unpacks fields from the current buf, reading field by field, and returning when complete */
int jdwp_unpackfv( jdwp_buffer* buf, char* format, va_list ap ){
	uint8_t *v8;
	uint16_t *v16;
	uint32_t *v32;
	uint64_t *v64;
	int err = 0;

	while(*format) {
		switch(*format++) {
		case '1':
			v8 = va_arg(ap, uint8_t*);
			err = jdwp_unpack_u8(buf, v8);
			break;
		case '2':
			v16 = va_arg(ap, uint16_t*);
			err = jdwp_unpack_u16(buf, v16);
			break;
		case '4':
			v32 = va_arg(ap, uint32_t*);
			err = jdwp_unpack_u32(buf, v32);
			break;
		case '8':
			v64 = va_arg(ap, uint64_t*);
			err = jdwp_unpack_u64(buf, v64);
			break;
		case 'i':
			v32 = va_arg(ap, uint32_t*);
			err = jdwp_unpack_u32(buf, v32);
			break;
		case 'l':
			v64 = va_arg(ap, uint64_t*);
			err = jdwp_unpack_u64(buf, v64);
			break;
		case 'o':
			v64 = va_arg(ap, uint64_t*);
			err = jdwp_unpack_id(buf, v64, buf->oSz);
			break;
		case 't':
			v64 = va_arg(ap, uint64_t*);
			err = jdwp_unpack_id(buf, v64, buf->tSz);
			break;
		case 'f':
			v64 = va_arg(ap, uint64_t*);
			err = jdwp_unpack_id(buf, v64, buf->fSz);
			break;
		case 's':
			v64 = va_arg(ap, uint64_t*);
			err = jdwp_unpack_id(buf, v64, buf->sSz);
			break;
		case 'm':
			v64 = va_arg(ap, uint64_t*);
			err = jdwp_unpack_id(buf, v64, buf->mSz);
			break;
		default:
			err = JDWP_OP_UNSUPPORTED;
		}
		if (err) break;
	};
	return err;
}
