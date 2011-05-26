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
import andbug.command
from getopt import getopt
from andbug.options import parse_mquery, format_mjni, parse_cpath
from Queue import Queue, Empty as QueueEmpty

@andbug.command.action('<class-path>')
def trace(ctxt, cpath):
    'reports calls to dalvik methods associated with a class'
    q = Queue()    

    cpath = parse_cpath(cpath)
    print '[::] setting hooks'
    for c in ctxt.proc.classes(cpath):
        c.hookEntries(q)
        print '[::] hooked', c
    print '[::] hooks set'

    while True:
        try:
            t, l = q.get()
            f = t.frames[0]
            print '[::]', t, f.loc
            for k,v in f.values.items():
                print '    ', k, '=', v
        finally:
            t.resume()
