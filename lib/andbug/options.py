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

