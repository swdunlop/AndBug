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

'''
Screed (plural Screeds)

1. A long discourse or harangue.
2. A piece of writing.
3. A tool, usually a long strip of wood or other material, for producing a smooth, flat surface on, for example, a concrete floor or a plaster wall.
4. A smooth flat layer of concrete or similar material.
5. A python module for formatting text output

Written language has evolved concurrent with the advent of movable type and
the information age, introducing a number of typographic conventions that are
used to impose structure.  The Screed format employs a subset of these 
conventions to structure output in way that is easily parsed by software or 
read in a terminal.

Screed is used by AndBug to format command output as well.

'''

import textwrap
import sys
import subprocess
import re
import andbug.log

rx_blocksep = re.compile('[\r\n][ \t]*[\r\n]+')
rx_linesep = re.compile('[\r\n][ \t]*')

def body(data):
    blocks = rx_blocksep.split(data.strip())

    for block in blocks:
        block = block.strip()
        block = rx_linesep.sub(' ', block)
        if not block: continue
        if block.startswith('-- '):
            item(block[3:])
        else:
            text(block)

def tput(attr, alt=None):
    p = subprocess.Popen(('tput', attr), stdout=subprocess.PIPE, stderr=None)
    p.wait()
    if p.returncode:
        return alt
    o, _ = p.communicate()
    return int(o)

class area(object):
    def __init__(self, title):
        self.title = title
        self.create()
    def __enter__(self):
        self.enter()
    def __exit__(self, *_):
        self.exit()
        return False

    def enter(self):
        pass 
    def exit(self):
        pass
    def create(self):
        pass

class section(area):
    def create(self):
        output().create_section(self.title)
    def enter(self):
        output().enter_section(self.title)
    def exit(self):
        output().exit_section(self.title)

class item(area):
    def create(self):
        output().create_item(self.title)
    def enter(self):
        output().enter_item(self.title)
    def exit(self):
        output().exit_item(self.title)

class meta(area):
    def create(self):
        output().create_item(self.title)
    def enter(self):
        output().enter_item(self.title)
    def exit(self):
        output().exit_item(self.title)

class refer(area):
    def create(self):
        output().create_refer(self.title)
    def enter(self):
        output().enter_refer(self.title)
    def exit(self):
        output().exit_refer(self.title)

def text(data):
    output().create_text(data)

def line(data, row=None):
    output().create_line(data, row)

def dump(data):
    output().create_dump(data)


class surface(object):
    def __init__(self, output=None):
        if output is None:
            output = sys.stdout
        self.output = output
        self.tty = self.output.isatty()
        self.indent = []
        self.textwrap = textwrap.TextWrapper()

    def __call__(self):
        return self

    @property
    def current_indent(self):
        return self.indent[-1] if self.indent else ''

    def push_indent(self, indent):
        self.indent.append(indent)       
        self.textwrap.subsequent_indent = indent

    def pop_indent(self):
        self.indent = self.indent[:-1]
        self.textwrap.subsequent_indent = self.current_indent

    def write(self, data):
        self.output.write(data)
    
    def newline(self):
        self.write('\n')

    def create_section(self, title):
        pass
                        
    def enter_section(self, title):
        pass

    def exit_section(self, title):
        pass

    def create_item(self, title):
        pass
                        
    def enter_item(self, title):
        pass

    def exit_item(self, title):
        pass

    def create_dump(self, data):
        width = self.width
        indent = self.current_indent

        if self.width is None:
            width = 16
        else:
            width -= len(self.indent)
            width -= 13 # overhead
            width = width / 4 # dd_c

        hex = andbug.log.format_hex(data, self.current_indent, width)
        self.write(hex)
        self.newline()

    def create_line(self, line, row = None):
        if row is None:
            self.wrap_line(self.current_indent + line)
        else:
            row = "%4i: " % row
            self.wrap_line(self.current_indent + row + line, " " * len(row))

    def wrap_line(self, line, indent=None):
        if self.width is None:
            self.write(line)
            self.newline()
            return
        if indent is not None:
            self.textwrap.subsequent_indent = indent
            lines = self.textwrap.wrap(line)
            self.textwrap.subsequent_indent = self.current_indent
        else:
            lines = self.textwrap.wrap(line)

        self.write('\n'.join(lines))
        self.newline()                

class scheme(object):
    def __init__(self, binds = []):
        self.c16 = {}
        self.c256 = {}

        for bind in binds:
            self.bind(*bind)

    def bind(self, tag, c16, c256 = None):
        if c16 > 7:
            c16 = '\x1B[1;3' + str(c16 - 8) + 'm'
        else:
            c16 = '\x1B[0;3' + str(c16) + 'm'

        if c256 is not None:
            c256 = '\x1B[38;05;' + str(c256) + 'm'
        else:
            c256 = c16

        self.c16[tag] = c16
        self.c256[tag] = c256

    def load(self, tag, depth):
        if not depth: return ''
        return (self.c256 if (depth == 256) else self.c16).get(tag, '\x1B[0m')

redmedicine = scheme((
    ('##',  9,  69),
    ('--', 15, 254),
    ('$$',  7, 146),
    ('::', 11, 228),
    ('//',  7, 242),
))

class ascii(surface):
    def __init__(self, output=None, width=None, depth=None, palette=redmedicine):
        surface.__init__(self, output)
        if width is None:
            width = 79
        if depth is None:
            depth = 16 if self.tty else 0
        self.width = width
        self.depth = depth
        if self.tty:
            self.pollcap()
        self.next_indent = None
        self.context = []
        self.prev_tag = ''
        self.palette = palette

    def transition(self, next):
        prev = self.prev_tag
        self.prev_tag = next
        #print "TRANSITION", repr(prev), "->", repr(next)

        if prev == '00':
            return # Nothing to do.
        elif next == '00':
            return # Also nothing to do.
        elif prev == '  ':
            return # first children are never set off.
        elif (prev == '$$') and (next == '$$'):
            self.newline()
        elif prev == next:  
            return # Identical children are not set off.
        else:
            self.newline()
            self.prev_tag = '00'

    def create_section(self, title):
        self.create_tagged_area( '##', title)

    def enter_section(self, title):
        self.enter_tagged_area()
    
    def exit_section(self, title):
        self.exit_tagged_area()

    def create_item(self, title):
        self.create_tagged_area( '--', title)

    def enter_item(self, title):
        self.enter_tagged_area()
    
    def exit_item(self, title):
        self.exit_tagged_area()

    def create_meta(self, title):
        self.create_tagged_area( '//', title)

    def enter_meta(self, title):
        self.enter_tagged_area()
    
    def exit_meta(self, title):
        self.exit_tagged_area()

    def create_refer(self, title):
        self.create_tagged_area( '::', title)

    def enter_refer(self, title):
        self.enter_tagged_area()
    
    def exit_refer(self, title):
        self.exit_tagged_area()

    def create_text(self, text):
        self.transition('$$')
        self.write(self.palette.load('$$', self.depth))
        self.wrap_line(self.current_indent + text)
        self.write("\x1B[01m")

    def create_tagged_area(self, tag, banner):
        self.transition(tag)
        self.write(self.palette.load(tag, self.depth))
        tag += ' '
        self.next_indent = self.current_indent + ' ' * len(tag)
        self.wrap_line(self.current_indent + tag + banner, self.next_indent)
        self.write("\x1B[0m")

    def enter_tagged_area(self):
        self.push_indent(self.next_indent)
        self.context.append(self.prev_tag)
        #print 'ENTER', repr(self.prev_tag), "-> '  '"
        self.prev_tag = '  '
    
    def exit_tagged_area(self):
        self.pop_indent()
        next = self.context.pop(-1)
        if self.prev_tag != '00':
            self.prev_tag = next
        #print 'EXIT ->', repr(self.prev_tag)

    def pollcap(self):
        if not self.tty: return
        self.width = tput('cols', self.width)
        self.depth = tput('colors', self.depth)        
        self.textwrap.width = self.width

OUTPUT = None
PALETTE = None

def scheme():
    if PALETTE is None:
        return redmedicine
    else:
        return PALETTE

def output():
    global OUTPUT
    if OUTPUT is None:
        OUTPUT = ascii(palette=scheme())
    return OUTPUT

if __name__ == '__main__':
    with section('Introduction'):
        text('''Since the sentence detection algorithm relies on string.lowercase for the definition of lowercase letter, and a convention of using two spaces after a period to separate sentences on the same line, it is specific to English-language texts.''')
        text('''If true, TextWrapper attempts to detect sentence endings and ensure that sentences are always separated by exactly two spaces. This is generally desired for text in a monospaced font. However, the sentence detection algorithm is imperfect: it assumes that a sentence ending consists of a lowercase letter followed by one of '.', '!', or '?', possibly followed by one of '"' or "'", followed by a space. One problem with this is algorithm is that it is unable to detect the difference.''')
    with section('Points of Interest'):
        item('''String that will be prepended to the first line of wrapped output. Counts towards the length of the first line.''')
        text('''this is some inbetween text''')
        item('''This is a much shorter item.''')
    with section('Data'):
        dump(open('/dev/urandom').read(1024))
    with section('Conclusion'):
        text('''The textwrap module provides two convenience functions, wrap() and fill(), as well as TextWrapper, the class that does all the work, and a utility function dedent(). If you're just wrapping or filling one or two text strings, the convenience functions should be good enough; otherwise, you should use an instance of TextWrapper for efficiency.''')

def pollcap():
    output().pollcap()
