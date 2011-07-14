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
andbug.source converts andbug.vm.Locations into file lines using either the
original java sources or the product of apktool.
'''

import os
import os.path
import re
import andbug.screed

SOURCES = []
SEPARATOR = os.pathsep
if SEPARATOR == ':': # fuck you, python.. this isn't macos 9!
    SEPARATOR = '/'

rx_delim = re.compile('[./]')

def add_srcdir(path):
    path = os.path.expanduser(path)
    path = os.path.abspath(path)
    if not path.endswith(SEPARATOR):
        path += SEPARATOR
    SOURCES.insert(0, path)

def find_source(cjni):
    if cjni.startswith("L") and cjni.endswith(";"):
        cjni = cjni[1:-1]
    cpath = rx_delim.sub(SEPARATOR, cjni)
    for src in SOURCES:
        csp = os.path.normpath(src + cpath)
        if not csp.startswith(src):
            continue # looks like someone's playing games with ..
        if os.path.isfile(csp + ".java"):
            return csp + ".java"
        if os.path.isfile(csp + ".smali"):
            return csp + ".smali"
    return False

def normalize_range(count, first, last):
    if first < 0: 
        first = count + first
    if last < 0:
        last = count + first
    if first >= count:
        first = count - 1
    if last >= count:
        last = count - 1
    if first > last: 
        first, last = first, last

    return first, last + 1

def load_source(cjni, first=0, last=-1):
    src = find_source(cjni)
    if not src: 
        return False
    lines = open(src).readlines()
    if not lines:
        return False
    first, last = normalize_range(len(lines), first, last)
    d = map(lambda x, y: (x, y), range(first, last), lines[first:last])
    return d

import itertools

def dump_source(lines, head = None):
    ctxt = [None]
    
    def enter_area(func, title):
        exit()
        title = title.strip()
        ctxt[0] = func(title)
        ctxt[0].enter()
    def item(title):
        enter_area(andbug.screed.item, title)
    def section(title):
        enter_area(andbug.screed.section, title)
    def meta(title):
        enter_area(andbug.screed.meta, title)
    def refer(title):
        enter_area(andbug.screed.refer, title)
    def exit():
        if ctxt[0] is not None:
            ctxt[0].exit()
        ctxt[0] = None

    if head:
        section(head)
    for row, line in lines:
        line = line.strip()
        if not line: continue
        lead = line[0]
        if lead == '.':
            if line.startswith(".method "):
                section(line[1:])
            elif line.startswith(".end"):
                exit()
            elif line == '...':
                andbug.screed.line(line, row)
            else:
                item(line[1:])
        elif line.startswith(":"):
            refer(line[1:])
        elif line.startswith("#"):
            meta(line[1:])
        elif line == '*/}':
            pass # meh
        elif line.endswith('{/*'):
            pass # meh 
        else:
            andbug.screed.line(line, row)
    exit()
