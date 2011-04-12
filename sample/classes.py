import andbug, sys

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

class ListClassesSuccEntry(andbug.process.Element):
	@classmethod
	def unpackFrom(impl, buf):
		return impl(*buf.unpack("1t$$i"))

	def __init__(self, tag, ref, jni, gen, status):
		self.tag = tag # kind of reference type
		self.ref = ref # loaded reference type
		self.jni = jni # jniSignature
		self.gen = gen # genericSignature 
		self.status = status # (ERROR | INITIALIZED | PREPARED | VERIFIED)

class ListClassesSucc(andbug.process.Success):
	@classmethod
	def unpackFrom(impl, buf):
		def unpackEntry(ix):
			return ListClassesSuccEntry.unpackFrom(buf)

		count = buf.unpackU32()
		entries = list(map(unpackEntry, range(0, count)))
		return impl(entries)

	def __init__(self, entries):
		self.entries = entries

class ListClasses(andbug.process.Request):
	CODE = 0x0114
	SUCCESS = ListClassesSucc

r = c.request(ListClasses())
for entry in r.entries:
	print entry.jni
