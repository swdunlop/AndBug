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
## THIS SOFTWARE IS PROVIDED BY SCOTT DUNLOP "AS IS" AND ANY EXPRESS OR 
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
   
import os, sys
from cStringIO import StringIO

def blocks(seq, sz):
	ofs = 0
	lim = len(seq)
	while ofs < lim:
		yield seq[ofs:ofs+sz]
		ofs += sz

def censor(seq):
	for ch in seq:
		if ch < '!': 
			yield '.'
		elif ch > '~':
			yield '.'
		else:
			yield ch

def format_hex(data, indent="", width=16, out=None):
	if out == None:
		out = StringIO()
		strout = True
	else:
		strout = False

	indent += "%08x:  "
	ofs = 0
	for block in blocks(data, width):
		out.write(indent % ofs)
		out.write(' '.join(map(lambda x: x.encode('hex'), block)))
		if len(block) < width:
			out.write( '   ' * (width - len(block)) )
		out.write('  ')
		out.write(''.join(censor(block)))
		out.write(os.linesep)
		ofs += len(block)

	if strout:
		return out.getvalue()

def parse_hex(dump, out=None):
	if out == None:
		out = StringIO()
		strout = True
	else:
		strout = False

	for row in dump.splitlines():
		row = row.strip().split('  ')
		block = row[1].strip().split(' ')
		block = ''.join(map(lambda x: chr(int(x, 16)), block))
		out.write(block)

	if strout:
		return out.getvalue()

class LogEvent(object):
	def __init__(self, time, tag, meta, data):
		self.time = time
		self.tag = tag
		self.meta = meta
		self.data = data or ''
	
	def __str__(self):
		return "%s %s %s\n%s" % (
			self.tag, self.time, self.meta, 
			format_hex(self.data, indent="    ")
		)

class LogWriter(object):
	def __init__(self, file=sys.stdout):
		self.file = file
		
	def writeEvent(self, evt):
		self.file.write(str(evt))

class LogReader(object):
	def __init__(self, file=sys.stdin):
		self.file = file
		self.last = None
	
	def readLine(self):
		if self.last is None:
			line = self.file.readline().rstrip()
		else:
			line = self.last
			self.last = None
		return line

	def pushLine(self, line):
		self.last = line

	def readEvent(self):
		line = self.readLine()
		if not line: return None
		if line[0] == ' ':
			return self.readEvent() # Again..
		 
		tag, time, meta = line.split(' ', 3)
		time = int(time)
		data = []

		while True:
			line = self.readLine()
			if line.startswith( '    ' ):
				data.append(line)
			else:
				self.pushLine(line)
				break
				
		if data:
			data = parse_hex('\n'.join(data))
		else:
			data = ''

		return LogEvent(time, tag, meta, data)

stderr = LogWriter(sys.stderr)
stdout = LogWriter(sys.stdout)

def error(tag, meta, data = None):
	stderr.writeEvent(LogEvent(now, meta, data))

def info(tag, meta, data = None):
	stdout.writeEvent(LogEvent(now, meta, data))

def read_log(path=None, file=None):
	if path is None:
		if file is None:
			reader = stdin
		else:
			reader = LogReader(sys.stdin)
