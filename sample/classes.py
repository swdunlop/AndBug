import andbug, sys
from collections import namedtuple

usage = '''
%s <portno>
Interrogates an Android process via a local ADB bridge, listing loaded classes.
'''

if len(sys.argv) != 2:
    print usage % (sys.argv[0],)
    sys.exit(0)

try:
    p = int(1919)
except:
    print usage % (sys.argv[0],)
    sys.exit(1)

c = andbug.connect('127.0.0.1', int(sys.argv[1]))

class_entry = namedtuple('class_entry', (
	'tag', 'ref', 'jni', 'gen', 'status'
))

def unpack_succ(buf):
	ct = buf.unpackU32()
	ls = [None,] * ct
	for i in range(0, ct):
		ls[i] = class_entry(*buf.unpack("1t$$i"))
	return ls

code, buf = c.request(0x0114)
if code:
	print "PROTOCOL-ERROR:", code
	sys.exit(1)

for entry in unpack_succ(buf):
	print entry.jni
