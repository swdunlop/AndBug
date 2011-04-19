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

import sys
from getopt import getopt
from andbug.process import Process
from andbug.options import parse_cname
from Queue import Queue, Empty as QueueEmpty

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

def main(args):
	if len(args) < 3: usage(args[0])
	mn, jni, args = parse_options(args[1:])
	if len(args) != 2: usage(args[0])

	port = int(args[0])
	cn = parse_cname(args[1])
	p = Process()
	p.connect(port)
	q = Queue()

	for l in p.classes(cn).methods(name=mn, jni=jni).get('firstLoc'):
		l.hook(q)
		print ':::: HOOKED', l

	print
	print
	print
	
	while True:
		try:
			t, l = q.get()
			f = t.frames[0]
			print '[::]', t, f.loc
			for k,v in f.values.items():
				print '    ', k, '=', v
		finally:
			t.resume()

if __name__ == '__main__':
	main(sys.argv)

