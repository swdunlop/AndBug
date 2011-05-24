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

class ParseError(Exception):
    def __init__(self, reason, option):
        self.reason = reason
        self.option = option

    def __str__(self):
        return '%s: %r.' % (self.reason, self.option)

def parse_cpath(path):
	if path.startswith('L') and path.endswith(';') and ('.' not in path):
		return path
	elif path.startswith('L') or path.endswith(';') or ('/' in path):
		raise ParseError('could not determine if path is a JNI or logical class path', path)
	else:
		return'L' + path.replace('.', '/') + ';'

def parse_mspec(mspec):
    if (mspec == '*') or (not mspec):
        return None, None
    
    s = mspec.find('(')
    if s < 0:
        return mspec, None

    return mspec[:s], mspec[s:]

def parse_mquery(cp, ms):
    #TODO: support class->method syntax.
    cp = parse_cpath(cp)
    mn, mj = parse_mspec(ms)
    return cp, mn, mj

'''
def parse_mpath(path):
    'given a JNI or logical method path, yields class-jni, meth-name, args-jni and retn-jni'

    if '(' in path:
        clsmet, argret = path.split('(', 1)    
    else:
        clsmet, argret = path, None
    
    if argret and (')' in argret):
        arg, ret = argret.rsplit(')', 1)    
    else:
        arg, ret = None, None
    
    if '.' in clsmet:
        cls, met = clsmet.rsplit('.', 1)
    elif ';' in clsmet:
        cls, met = clsmet.rsplit(';', 1)
        cls += ';'
    else:
        cls, met = None, clsmet

    if cls is not None:
        cls = parse_cpath(cls)
                
    return cls, met, arg, ret
'''

def format_mjni(name, args, retn):
    return '%s(%s)%s' % (name, args, retn)

