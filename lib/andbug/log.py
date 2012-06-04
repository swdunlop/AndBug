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
   
import os, sys, time
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
    now = int(time.time())
    stderr.writeEvent(LogEvent(now, tag, meta, data))

def info(tag, meta, data = None):
    now = int(time.time())
    stdout.writeEvent(LogEvent(now, tag, meta, data))

def read_log(path=None, file=None):
    if path is None:
        if file is None:
            reader = LogReader(sys.stdin)
        else:
            reader = LogReader(file)
    return reader
