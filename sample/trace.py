C_THREAD = 3
C_CLASS = 4
C_LOCATION = 7

EK_METHOD_ENTRY = 40
EK_METHOD_EXIT = 41

SP_NONE = 0
SP_THREAD = 1
SP_PROCESS = 2

from andbug.process import Failure
from andbug.options import parse_cname

def pack_setevt(buf, kind, policy, modifiers):
	buf.pack('11i', kind, policy, len(modifiers))
	
	for mod in modifiers:
		k = mod[0]
		buf.packU8(k)
		if k == C_THREAD: # thread-requirement
			buf.pack('o', mod[1])
		elif k == C_CLASS: # class-requirement
			buf.pack('t', mod[1]) 
		elif k == C_LOCATION: # location-requirement
			buf.pack('1tm8', mod[2], mod[3], mod[4], mod[5])
		else:
			raise Failure('unrecognized modifier %s' % mod)

def parse_options(opts):
	name, jni = None, None
	opts, args = getopt(sys.argv[1:], 'n:j:')
	for opt, val in opts:
		if opt == '-n':
			name = name
		elif opt == '-j':
			jni = val
	return name, jni, args

def usage(name):
	print 'usage: %s [-n method-name] [-j method-jni-signature] port class' % name
	print '   ex: %s -n <init> 9012 java.net.URL' % name
	print ''
	sys.exit(2)

def method_line_table(conn, cid, mid):
	data = conn.buffer().pack('tm', cid, mid)
	code, buf = conn.request(0x0601, data)
	if code != 0: raise Failure(code)
	first, last, count = buf.unpack('88i')
	#TODO
	return first, last

def trace(conn, cid, mid):
	buf = self.proc.conn.buffer()
	loc = method_line_table(conn, cid, mid)[0]
	pack_setevt( buf, EK_METHOD_ENTRY, SP_NONE, (
		(C_CLASS, cid),
		(C_LOCATION, loc)
	))
	code, data = self.proc.conn.request(0x1501, buf.data())

def main(args):
	if len(args) < 3: usage(args[0])
	mn, jni, args = parse_options(args[1:])
	if len(args) != 2: usage(args[0])

	port = int(args[0])
	cn = parse_cname(args[1])
	p = Process(port)
	for m in p.classes(cn).methods(name=mn, jni=jni):
		trace(p.conn, m.cid, m.mid)
	

	#TODO: identify matching methods
	#TODO: set a break on each method
	trace(conn, cid, mid)

if __name__ == '__main__':
	main(sys.argv)
