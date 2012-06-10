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

import andbug, andbug.data, andbug.proto, andbug.errors
import threading, re
from andbug.data import defer
from threading import Lock
from Queue import Queue

## Implementation Questions:
## -- unpackFrom methods are used to unpack references to an element from
##    a JDWP buffer.  This does not mean unpacking the actual definition of
##    the element, which tends to be one-shot.
##
## References:
## -- All codes that are sent to Dalvik VM where extracted from
##    dalvik/vm/jdwp/JdwpHandler.cpp and converted to HEX values
##    (e.g. Resume Thread: {11, 3, ....} => 0b03)
## -- JDWP Protocol:
##    dalvik implements a subset of these, verify with JdwpHandler.cpp:
##    http://docs.oracle.com/javase/6/docs/platform/jpda/jdwp/jdwp-protocol.html
##    

class RequestError(Exception):
    'raised when a request for more information from the process fails'
    def __init__(self, code):
        Exception.__init__(self, 'request failed, code %s' % code)
        self.code = code

class Element(object):
    def __repr__(self):
        return '<%s>' % self

    def __str__(self):
        return '%s:%s' % (type(self).__name__, id(self))

class SessionElement(Element):
    def __init__(self, sess):
        self.sess = sess

    @property
    def conn(self):
        return self.sess.conn

class Field(SessionElement):
    def __init__(self, session, fid):
        SessionElement.__init__(self, session)
        self.fid = fid
    
    @classmethod 
    def unpackFrom(impl, sess, buf):
        return sess.pool(impl, sess, buf.unpackFieldId())
    
    @property
    def public(self):
        return self.flags & 0x0001
    
    @property
    def private(self):
        return self.flags & 0x0002
    
    @property
    def protected(self):
        return self.flags & 0x0004
    
    @property
    def static(self):
        return self.flags & 0x0008
    
    @property
    def final(self):
        return self.flags & 0x0010

    @property
    def volatile(self):
        return self.flags & 0x0040
    
    @property
    def transient(self):
        return self.flags & 0x0080
    
class Value(SessionElement):
    @property
    def isPrimitive(self):
        return self.TAG in PRIMITIVE_TAGS

    @property
    def isObject(self):
        return self.TAG in OBJECT_TAGS

class Frame(SessionElement):
    def __init__(self, sess, fid):
        SessionElement.__init__(self, sess)
        self.fid = fid
        self.loc = None
        self.tid = None

    def __str__(self):
        return 'frame %s, at %s' % (self.fid, self.loc)   

    @classmethod 
    def unpackFrom(impl, sess, buf):
        return sess.pool(impl, sess, buf.unpackFrameId())
    
    def packTo(self, buf):
        buf.packFrameId(self.fid)

    @property
    def native(self):
        return self.loc.native

    @property
    def values(self):
        vals = {}
        if self.native: return vals
        
        sess = self.sess
        conn = self.conn
        buf = conn.buffer()
        buf.packObjectId(self.tid)
        buf.packFrameId(self.fid)
        slots = self.loc.slots
        buf.packInt(len(slots))

        for slot in slots:
            buf.packInt(slot.index)
            buf.packU8(slot.tag) #TODO: GENERICS

        code, buf = conn.request(0x1001, buf.data())
        if code != 0:
            raise RequestError(code)
        ct = buf.unpackInt()

        for x in range(0, ct):
            s = slots[x]
            vals[s.name] = unpack_value(sess, buf)

        return vals

    def value(self, name):
        if self.native: return None

        sess = self.sess
        conn = self.conn
        buf = conn.buffer()
        buf.packObjectId(self.tid)
        buf.packFrameId(self.fid)
        slots = self.loc.slots
        buf.packInt(1)

        loc = None
        for i in range(0, len(slots)):
            if slots[i].name == name:
                loc = i
                break
            else:
                continue

        if loc is None:
            return None
        slot = slots[loc]
        buf.packInt(slot.index)
        buf.packU8(slot.tag) #TODO: GENERICS

        code, buf = conn.request(0x1001, buf.data())
        if code != 0:
            raise RequestError(code)
        if buf.unpackInt() != 1:
            return None

        return unpack_value(sess, buf)

    def setValue(self, name, value):
        if self.native: return False

        sess = self.sess
        conn = self.conn
        buf = conn.buffer()
        buf.packObjectId(self.tid)
        buf.packFrameId(self.fid)
        slots = self.loc.slots
        buf.packInt(1)

        loc = None
        for i in range(0, len(slots)):
            if slots[i].name == name:
                loc = i
                break
            else:
                continue

        if loc is None:
            return False
        slot = slots[loc]
        buf.packInt(slot.index)
        pack_value(sess, buf, value, slot.jni) #TODO: GENERICS

        code, buf = conn.request(0x1002, buf.data())
        if code != 0:
            raise RequestError(code)

        return True

class Thread(SessionElement):
    #TODO: promote to Value
    def __init__(self, sess, tid):
        SessionElement.__init__(self, sess)
        self.tid = tid
    
    def __str__(self):
        tStatus, sStatus = self.status
        return 'thread %s\t(%s %s)' % (self.name or hex(self.tid), Thread.threadStatusStr(tStatus), Thread.suspendStatusStr(sStatus))

    def suspend(self):  
        conn = self.conn
        buf = conn.buffer()
        buf.packObjectId(self.tid)
        code, buf = conn.request(0x0b02, buf.data())
        if code != 0:
            raise RequestError(code)

    def resume(self):
        conn = self.conn
        buf = conn.buffer()
        buf.packObjectId(self.tid)
        code, buf = conn.request(0x0b03, buf.data())
        if code != 0:
            raise RequestError(code)

    def packTo(self, buf):
        buf.packObjectId(self.tid)

    def hook(self, func = None, queue = None):
        conn = self.conn
        buf = conn.buffer()
        # 40:EK_METHOD_ENTRY, 1: SP_THREAD, 1 condition of type ClassRef (3), ThreadId
        buf.pack('11i1t', 40, 1, 1, 3, self.tid) 
        code, buf = conn.request(0x0f01, buf.data())
        if code != 0:
            raise RequestError(code)
        eid = buf.unpackInt()
        return self.sess.hook(eid, func, queue, self)

    @classmethod
    def unpackFrom(impl, sess, buf):
        tid = buf.unpackObjectId()
        return sess.pool(impl, sess, tid)

    @property
    def frames(self):
        tid = self.tid
        sess = self.sess
        conn = self.conn
        buf = conn.buffer()
        buf.pack('oii', self.tid, 0, -1)
        code, buf = conn.request(0x0b06, buf.data())
        if code != 0:
            raise RequestError(code)
        ct = buf.unpackInt()

        def load_frame():
            f = Frame.unpackFrom(sess, buf)
            f.loc = Location.unpackFrom(sess, buf)
            f.tid = tid
            return f

        return andbug.data.view(load_frame() for i in range(0,ct))

    @property
    def frameCount(self):   
        conn = self.conn
        buf = conn.buffer()
        buf.packObjectId(self.tid)
        code, buf = conn.request(0x0b07, buf.data())
        if code != 0:
            raise RequestError(code)
        return buf.unpackInt()

    @property
    def name(self): 
        conn = self.conn
        buf = conn.buffer()
        buf.packObjectId(self.tid)
        code, buf = conn.request(0x0b01, buf.data())
        if code != 0:
            raise RequestError(code)
        return buf.unpackStr()

    @property
    def status(self):
        conn = self.conn
        buf = conn.buffer()
        buf.packObjectId(self.tid)
        code, buf = conn.request(0x0b04, buf.data())
        if code != 0:
            raise RequestError(code)

        threadStatus = buf.unpackInt()
        suspendStatus = buf.unpackInt()

        return threadStatus, suspendStatus

    @staticmethod
    def threadStatusStr(tStatus):
        szTS = ('zombie', 'running', 'sleeping', 'monitor', 'waiting', 'initializing', 'starting', 'native', 'vmwait')
        tStatus = int(tStatus)
        if tStatus < 0 or tStatus >= len(szTS):
            return "UNKNOWN"
        return szTS[tStatus]

    @staticmethod
    def suspendStatusStr(sStatus):
        szSS = ('running', 'suspended')
        sStatus = int(sStatus)
        if sStatus < 0 or sStatus >= len(szSS):
            return "UNKNOWN"
        return szSS[sStatus]

class Location(SessionElement):
    def __init__(self, sess, tid, mid, loc):
        SessionElement.__init__(self, sess)
        self.tid = tid
        self.mid = mid
        self.loc = loc
        self.line = None

    def __str__(self):
        if self.loc >= 0:
            return '%s:%i' % (self.method, self.loc)
        else:
            return str(self.method)

    def packTo(self, buf):
        c = self.klass
        buf.ipack('1tm8', c.tag, self.tid, self.mid, self.loc)

    @classmethod
    def unpackFrom(impl, sess, buf):
        tag, tid, mid, loc = buf.unpack('1tm8')
        return sess.pool(impl, sess, tid, mid, loc)

    def hook(self, func = None, queue = None):
        conn = self.conn
        buf = conn.buffer()
        # 2: BREAKPOINT
        # 40:METHOD_ENTRY
        # 41:METHOD_EXIT
        if self == self.method.firstLoc:
            eventKind = 40
        elif self == self.method.lastLoc:
            eventKind = 41
        else:
            eventKind = 2
        # 1: SP_THREAD, 1 condition of type Location (7)
        buf.pack('11i1', eventKind, 1, 1, 7)

        self.packTo(buf)
        code, buf = conn.request(0x0f01, buf.data())
        if code != 0:
            raise RequestError(code)
        eid = buf.unpackInt()
        return self.sess.hook(eid, func, queue, self)

    @property
    def native(self):
        return self.loc == -1

    @property
    def method(self):
        return self.sess.pool(Method, self.sess, self.tid, self.mid)

    @property
    def klass(self):
        return self.sess.pool(Class, self.sess, self.tid)

    @property
    def slots(self):
        l = self.loc
        def filter_slots():
            for slot in self.method.slots:
                f = slot.firstLoc
                if f > l: continue
                if l - f > slot.locLength: continue
                yield slot
        return tuple() if self.native else tuple(filter_slots())

class Slot(SessionElement):
    def __init__(self, sess, tid, mid, index):
        SessionElement.__init__(self, sess)
        self.tid = tid
        self.mid = mid
        self.index = index
        self.name = None

    def __str__(self):
        if self.name:
            return 'slot %s at index %i' % (self.name, self.index)
        else:
            return 'slot at index %i' % (self.index)

    def load_slot(self):
        self.sess.pool(Class, self.sess, self.tid).load_slots()

    firstLoc = defer(load_slot, 'firstLoc')
    locLength = defer(load_slot, 'locLength')
    name = defer(load_slot, 'name')
    jni = defer(load_slot, 'jni')
    gen = defer(load_slot, 'gen')

    @property
    def tag(self):
        return ord(self.jni[0])

class Method(SessionElement):
    def __init__(self, sess, tid, mid):
        SessionElement.__init__(self, sess)
        self.tid = tid
        self.mid = mid

    @property
    def klass(self):
        return self.sess.pool(Class, self.sess, self.tid)

    def __str__(self):
        return '%s.%s%s' % (
            self.klass, self.name, self.jni 
    )       
     
    def __repr__(self):
        return '<method %s>' % self

    def load_line_table(self):
        sess = self.sess
        conn = sess.conn
        pool = sess.pool
        tid = self.tid
        mid = self.mid
        data = conn.buffer().pack('om', tid, mid)
        code, buf = conn.request(0x0601, data)
        if code != 0: raise RequestError(code)
        
        f, l, ct = buf.unpack('88i')
        if (f == -1) or (l == -1):             
            self.firstLoc = None
            self.lastLoc = None
            self.lineTable = andbug.data.view([])
            #TODO: How do we handle native methods?
 
        self.firstLoc = pool(Location, sess, tid, mid, f)
        self.lastLoc = pool(Location, sess, tid, mid, l)

        ll = {}
        self.lineTable = ll
        def line_loc():
            loc, line  = buf.unpack('8i')
            loc = pool(Location, sess, tid, mid, loc)
            loc.line = line
            ll[line] = loc

        for i in range(0,ct):
            line_loc()
    
    firstLoc = defer(load_line_table, 'firstLoc')
    lastLoc = defer(load_line_table, 'lastLoc')
    lineTable = defer(load_line_table, 'lineTable')

    def load_method(self):
        self.klass.load_methods()

    name = defer(load_method, 'name')
    jni = defer(load_method, 'jni')
    gen = defer(load_method, 'gen')
    flags = defer(load_method, 'flags' )

    def load_slot_table(self):
        sess = self.sess
        conn = self.conn
        pool = sess.pool
        tid = self.tid
        mid = self.mid
        data = conn.buffer().pack('om', tid, mid)
        code, buf = conn.request(0x0605, data)
        if code != 0: raise RequestError(code)
    
        act, sct = buf.unpack('ii')
        #TODO: Do we care about the argCnt ?
         
        def load_slot():
            codeIndex, name, jni, gen, codeLen, index  = buf.unpack('l$$$ii')
            slot = pool(Slot, sess, tid, mid, index)
            slot.firstLoc = codeIndex
            slot.locLength = codeLen
            slot.name = name
            slot.jni = jni
            slot.gen = gen

            return slot

        self.slots = andbug.data.view(load_slot() for i in range(0,sct))

    slots = defer(load_slot_table, 'slots')

class RefType(SessionElement):
    def __init__(self, sess, tag, tid):
        SessionElement.__init__(self, sess)
        self.tag = tag
        self.tid = tid
    
    def __repr__(self):
        return '<type %s %s#%x>' % (self.jni, chr(self.tag), self.tid)

    def __str__(self):
        return repr(self)

    @classmethod 
    def unpackFrom(impl, sess, buf):
        return sess.pool(impl, sess, buf.unpackU8(), buf.unpackTypeId())

    def packTo(self, buf):
        buf.packObjectId(self.tid)

    def load_signature(self):
        conn = self.conn
        buf = conn.buffer()
        self.packTo(buf)
        code, buf = conn.request(0x020d, buf.data())
        if code != 0:
            raise RequestError(code)
        self.jni = buf.unpackStr()
        self.gen = buf.unpackStr()

    gen = defer(load_signature, 'gen')
    jni = defer(load_signature, 'jni')

    def load_fields(self):
        sess = self.sess
        conn = self.conn
        buf = conn.buffer()
        buf.pack("t", self.tid)
        code, buf = conn.request(0x020e, buf.data())
        if code != 0:
            raise RequestError(code)

        ct = buf.unpackU32()

        def load_field():
            field = Field.unpackFrom(sess, buf)
            name, jni, gen, flags = buf.unpack('$$$i')
            field.name = name
            field.jni = jni
            field.gen = gen
            field.flags = flags
            return field
        
        self.fieldList = andbug.data.view(
            load_field() for i in range(ct)
        )        

    fieldList = defer(load_fields, 'fieldList')

    @property
    def statics(self):
        sess = self.sess
        conn = self.conn
        buf = conn.buffer()
        buf.packTypeId(self.tid)
        fields = list(f for f in self.fieldList if f.static)
        buf.packInt(len(fields))
        for field in fields:
            buf.packFieldId(field.fid)
        code, buf = conn.request(0x0206, buf.data())
        if code != 0:
            raise RequestError(code)
        ct = buf.unpackInt()

        vals = {}
        for x in range(ct):
            f = fields[x]
            vals[f.name] = unpack_value(sess, buf)
        return vals

    def load_methods(self):
        tid = self.tid
        sess = self.sess
        conn = self.conn
        pool = sess.pool
        buf = conn.buffer()
        buf.pack("t", tid)
        code, buf = conn.request(0x020f, buf.data())
        if code != 0:
            raise RequestError(code)

        ct = buf.unpackU32()
                
        def load_method():
            mid, name, jni, gen, flags = buf.unpack('m$$$i')
            obj = pool(Method, sess, tid, mid)
            obj.name = name
            obj.jni = jni
            obj.gen = gen
            obj.flags = flags
            return obj
    
        self.methodList = andbug.data.view(
            load_method() for i in range(0, ct)
        )
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

class Class(RefType): 
    def __init__(self, sess, tid):
        RefType.__init__(self, sess, 'L', tid)
        
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return '<class %s>' % self

    def hookEntries(self, func = None, queue = None):
        conn = self.conn
        buf = conn.buffer()
        # 40:EK_METHOD_ENTRY, 1: SP_THREAD, 1 condition of type ClassRef (4)
        buf.pack('11i1t', 40, 1, 1, 4, self.tid) 
        code, buf = conn.request(0x0f01, buf.data())
        if code != 0:
            raise RequestError(code)
        eid = buf.unpackInt()
        return self.sess.hook(eid, func, queue, self)
        
    #def load_class(self):
    #   self.sess.load_classes()
    #   assert self.tag != None
    #   assert self.flags != None

    #tag = defer(load_class, 'tag')
    #jni = defer(load_class, 'jni')
    #gen = defer(load_class, 'gen')
    #flags = defer(load_class, 'flags')

class Hook(SessionElement):
    def __init__(self, sess, ident, func = None, queue = None, origin = None):
        SessionElement.__init__(self, sess)
        if queue is not None:
            self.queue = queue
        elif func is None:
            self.queue = queue or Queue()
        self.func = func        

        self.ident = ident
        self.origin = origin
        #TODO: unclean
        with self.sess.ectl:
            self.sess.emap[ident] = self

    def __str__(self):
        return ('<%s> %s %s' %
            (str(self.ident), str(self.origin), str(type(self.origin))))

    def put(self, data):
        if self.func is not None:
            return self.func(data)
        else:
            return self.queue.put(data)
            
    def get(self, block = False, timeout = None):
        return self.queue.get(block, timeout)

    def clear(self):
        #TODO: unclean
        conn = self.conn
        buf = conn.buffer()
        # 40:EK_METHOD_ENTRY
        buf.pack('1i', 40, int(self.ident))
        # 0x0f02 = {15, 2} EventRequest.Clear
        code, unknown = conn.request(0x0f02, buf.data())
        # fixme: check what a hell is the value stored in unknown
        if code != 0:
            raise RequestError(code)

        with self.sess.ectl:
            del self.sess.emap[self.ident]

unpack_impl = [None,] * 256

def register_unpack_impl(ek, fn):
    unpack_impl[ek] = fn

def unpack_events(sess, buf):
    sp, ct = buf.unpack('1i')
    for i in range(0, ct):
        ek = buf.unpackU8()
        im = unpack_impl[ek]
        if im is None:
            raise RequestError(ek)
        else:
            yield im(sess, buf)

def unpack_event_location(sess, buf):
    rid = buf.unpackInt()
    t = Thread.unpackFrom(sess, buf)
    loc = Location.unpackFrom(sess, buf)
    return rid, t, loc

# Breakpoint
register_unpack_impl(2, unpack_event_location)
# MothodEntry
register_unpack_impl(40, unpack_event_location)
# MothodExit
register_unpack_impl(41, unpack_event_location)

class Session(object):
    def __init__(self, conn):
        self.pool = andbug.data.pool()
        self.conn = conn
        self.emap = {}
        self.ectl = Lock()
        self.evtq = Queue()
        conn.hook(0x4064, self.evtq)
        self.ethd = threading.Thread(
            name='Session', target=self.run
        )
        self.ethd.daemon=1
        self.ethd.start()

    def run(self):
        while True:
            self.processEvent(*self.evtq.get())

    def hook(self, ident, func = None, queue = None, origin = None):
        return Hook(self, ident, func, queue, origin)

    def processEvent(self, ident, buf):
        pol, ct = buf.unpack('1i')

        for i in range(0,ct):
            ek = buf.unpackU8()
            im = unpack_impl[ek]
            if im is None:
                raise RequestError(ek)
            evt = im(self, buf)
            with self.ectl:
                hook = self.emap.get(evt[0])
            if hook is not None:
                hook.put(evt[1:])
                          
    def load_classes(self):
        code, buf = self.conn.request(0x0114)
        if code != 0:
            raise RequestError(code)

        def load_class():
            tag, tid, jni, gen, flags = buf.unpack('1t$$i')
            obj = self.pool(Class, self, tid)
            obj.tag = tag
            obj.tid = tid
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
    
    def suspend(self):
        code, buf = self.conn.request(0x0108, '')
        if code != 0:
            raise RequestError(code)

    @property
    def count(self):
        code, buf = self.conn.request(0x0108, '')
        if code != 0:
            raise RequestError(code)

    def resume(self):
        code, buf = self.conn.request(0x0109, '')
        if code != 0:
            raise RequestError(code)

    def exit(self, code = 0):
        conn = self.conn
        buf = conn.buffer()
        buf.pack('i', code)
        code, buf = conn.request(0x010A, '')
        if code != 0:
            raise RequestError(code)

    def threads(self, name=None):
        pool = self.pool
        code, buf = self.conn.request(0x0104, '')
        if code != 0:
            raise RequestError(code)
        ct = buf.unpackInt()

        def load_thread():
            tid = buf.unpackObjectId()
            return pool(Thread, self, tid)

        seq = (load_thread() for x in range(0,ct))
        if name is not None:
            if rx_dalvik_tname.match(name):
                seq = (t for t in seq if t.name == name)
            else:
                name = str(name)
                name = name if not re.match('^\d+$', name) else '<' + name + '>'
                seq = (t for t in seq if name in t.name.split(' ',1))
        return andbug.data.view(seq)

rx_dalvik_tname = re.compile('^<[0-9]+> .*$')

class Object(Value):
    def __init__(self, sess, oid):
        if oid == 0: raise andbug.errors.VoidError()
        SessionElement.__init__(self, sess)
        self.oid = oid

    def __repr__(self):
        return '<obj %s #%x>' % (self.jni, self.oid)
    
#    def __str__(self):
#        return str(self.fields.values())
    def __str__(self):
        return str("%s <%s>" % (str(self.jni), str(self.oid)))
        
    @classmethod
    def unpackFrom(impl, sess, buf):
        oid = buf.unpackObjectId()
        # oid = 0 indicates a GC omgfuckup in Dalvik
        # which is NOT as uncommon as we would like..
        if not oid: return None 
        return sess.pool(impl, sess, oid)

    def packTo(self, buf):
        buf.packObjectId(self.oid)

    @property
    def gen(self):
        return self.refType.gen
    
    @property
    def jni(self):
        return self.refType.jni

    def load_refType(self):
        conn = self.sess.conn
        buf = conn.buffer()
        self.packTo(buf)
        code, buf = conn.request(0x0901, buf.data())
        if code != 0:
            raise RequestError(code)
        self.refType = RefType.unpackFrom(self.sess, buf)
    
    refType = defer(load_refType, 'refType')

    @property
    def fieldList(self):
        r = list(f for f in self.refType.fieldList if not f.static)
        return r

    @property
    def typeTag(self):
        return self.refType.tag

    @property
    def fields(self):
        sess = self.sess
        conn = self.conn
        buf = conn.buffer()
        buf.packTypeId(self.oid)
        fields = self.fieldList
        buf.packInt(len(fields))
        for field in fields:
            buf.packFieldId(field.fid)
        code, buf = conn.request(0x0902, buf.data())
        if code != 0:
            raise RequestError(code)
        ct = buf.unpackInt()
        vals = {}
        for x in range(ct):
            f = fields[x]
            vals[f.name] = unpack_value(sess, buf)

        return vals

    def field(self, name):
        sess = self.sess
        conn = self.conn
        buf = conn.buffer()
        buf.packTypeId(self.oid)
        fields = self.fieldList
        buf.packInt(1)

        loc = None
        for i in range(0, len(fields)):
            if fields[i].name == name:
                loc = i
                break
            else:
                continue

        if loc is None:
            return None
        field = fields[loc]
        buf.packFieldId(field.fid)
        code, buf = conn.request(0x0902, buf.data())
        if code != 0:
            raise RequestError(code)
        if buf.unpackInt() != 1:
            return None
        return unpack_value(sess, buf)


    def setField(self, name, value):
        sess = self.sess
        conn = self.conn
        buf = conn.buffer()
        buf.packTypeId(self.oid)
        fields = self.fieldList
        buf.packInt(1)

        loc = None
        for i in range(0, len(fields)):
            if fields[i].name == name:
                loc = i
                break
            else:
                continue

        if loc is None:
            return None
        field = fields[loc]
        buf.packFieldId(field.fid)
        #TODO: WTF: ord(field.jni) !?
        pack_value(sess, buf, value, field.jni[0])
        code, buf = conn.request(0x0903, buf.data())
        if code != 0:
            raise RequestError(code)
        return True

## with andbug.screed.item(str(obj)):
##     if hasattr(obj, 'dump'):
##        obj.dump()

class Array(Object):
    def __repr__(self):
        data = self.getSlice()

        # Java very commonly uses character and byte arrays to express
        # text instead of strings, because they are mutable and have 
        # different encoding implications.

        if self.jni == '[C':
            return repr(''.join(data))
        elif self.jni == '[B':
            return repr(''.join(chr(c) for c in data))
        else:
            return repr(data)

    def __getitem__(self, index):
        if index < 0:
            self.getSlice(index-1, index)
        else:
            return self.getSlice(index, index+1)
    
    def __len__(self):
        return self.length
    
    def __iter__(self): return iter(self.getSlice())

    def __str__(self):
        return str(self.getSlice())
        
    @property
    def length(self):
        conn = self.conn
        buf = conn.buffer()
        self.packTo(buf)
        code, buf = conn.request(0x0d01, buf.data())        
        if code != 0:
            raise RequestError(code)
        return buf.unpackInt()

    def getSlice(self, first=0, last=-1):
        length = self.length
        if first > length:
            raise IndexError('first offset (%s) past length of array' % first)
        if last > length:
            raise IndexError('last offset (%s) past length of array' % last)
        if first < 0:
            first = length + first + 1
            if first < 0:
                raise IndexError('first absolute (%s) past length of array' % first)
        if last < 0:
            last = length + last + 1
            if last < 0:
                raise IndexError('last absolute (%s) past length of array' % last)
        if first > last:
            first, last = last, first
        
        count = last - first
        if not count: return []

        conn = self.conn
        buf = conn.buffer()
        self.packTo(buf)
        buf.packInt(first)
        buf.packInt(count)
        code, buf = conn.request(0x0d02, buf.data())
        if code != 0:
            raise RequestError(code)
        tag = buf.unpackU8()
        ct = buf.unpackInt()
        
        sess = self.sess
        if tag in OBJECT_TAGS:
            return tuple(unpack_value(sess, buf) for i in range(ct))
        else:
            return tuple(unpack_value(sess, buf, tag) for i in range(ct))

PRIMITIVE_TAGS = set(ord(c) for c in 'BCFDIJSVZ')
OBJECT_TAGS = set(ord(c) for c in 'stglcL')

class String(Object):
    def __repr__(self):
        return '#' + repr(str(self))

    def __str__(self):
        return self.data

    @property
    def data(self):
        conn = self.conn
        buf = conn.buffer()
        self.packTo(buf)
        code, buf = conn.request(0x0A01, buf.data())
        if code != 0:
            raise RequestError(code)
        return buf.unpackStr()

unpack_value_impl = [None,] * 256
def register_unpack_value(tag, func):
    for t in tag:
        unpack_value_impl[ord(t)] = func

register_unpack_value('B', lambda p, b: b.unpackU8())
register_unpack_value('C', lambda p, b: chr(b.unpackU8()))
register_unpack_value('F', lambda p, b: b.unpackFloat()) #TODO: TEST
register_unpack_value('D', lambda p, b: b.unpackDouble()) #TODO:TEST
register_unpack_value('I', lambda p, b: b.unpackInt())
register_unpack_value('J', lambda p, b: b.unpackLong())
register_unpack_value('S', lambda p, b: b.unpackShort()) #TODO: TEST
register_unpack_value('V', lambda p, b: b.unpackVoid())
register_unpack_value('Z', lambda p, b: (True if b.unpackU8() else False))
register_unpack_value('L', Object.unpackFrom)
register_unpack_value('tglc', Object.unpackFrom) #TODO: IMPL
register_unpack_value('s', String.unpackFrom)
register_unpack_value('[', Array.unpackFrom)

def unpack_value(sess, buf, tag = None):
    if tag is None: tag = buf.unpackU8()
    fn = unpack_value_impl[tag]
    if fn is None:
        raise RequestError(tag)
    else:
        return fn(sess, buf)

pack_value_impl = [None,] * 256
def register_pack_value(tag, func):
    for t in tag:
        pack_value_impl[ord(t)] = func

register_pack_value('B', lambda p, b, v: b.packU8(int(v)))
register_pack_value('F', lambda p, b, v: b.packFloat(float(v))) #TODO: TEST
register_pack_value('D', lambda p, b, v: b.packDouble(float(v))) #TODO:TEST
register_pack_value('I', lambda p, b, v: b.packInt(int(v)))
register_pack_value('J', lambda p, b, v: b.packLong(long(v)))
register_pack_value('S', lambda p, b, v: b.packShort(int(v))) #TODO: TEST
register_pack_value('V', lambda p, b, v: b.packVoid())
register_pack_value('Z', lambda p, b, v: b.packU8(bool(v) and 1 or 0))
#register_pack_value('s', lambda p, b, v: b.packStr(v)) # TODO: pack String

def pack_value(sess, buf, value, tag = None):
    if not tag:
        raise RequestError(tag)
    if isinstance(tag, basestring):
        tag = ord(tag[0])
    print "PACK", repr(tag), repr(value)
    fn = pack_value_impl[tag]
    if fn is None:
        raise RequestError(tag)
    else:
        buf.packU8(tag)
        return fn(sess, buf, value)

def connect(pid, dev=None):
    'connects using proto.forward() to the process associated with this context'
    conn = andbug.proto.connect(andbug.proto.forward(pid, dev))
    return andbug.vm.Session(conn)

