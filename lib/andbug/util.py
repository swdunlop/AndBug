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

import subprocess, threading, os, os.path
from cStringIO import StringIO

class ShellException( Exception ):
    def __init__( self, command, output, status ):
        self.command = command
        self.output = output
        self.status = status

def printout( prefix, data ):
    data = data.rstrip()
    if not data: return ''
    print prefix + data.replace( '\n', '\n' + prefix )

def sh( command, no_echo=True, no_fail=False, no_wait=False ):
    if not no_echo: 
        printout( '>>> ', repr( command ) )

    process = subprocess.Popen( 
        command,
        stdout = subprocess.PIPE,
        stderr = subprocess.STDOUT,
        stdin = None,
        shell = True if isinstance( command, str ) else False
    )
    
    if no_wait: return process

    output, _ = process.communicate( )
    status = process.returncode

    if status: 
        if not no_echo: printout( '!!! ', output )
        if not no_fail: raise ShellException( command, output, status )
    else:
        if not no_echo: printout( '::: ', output )

    return output

def which( utility ):
    for path in os.environ['PATH'].split( os.pathsep ):
        path = os.path.expanduser( os.path.join( path, utility ) )
        if os.path.exists( path ):
            return path

def test( command, no_echo=False ):
    process = subprocess.Popen( 
        command,
        stdout = subprocess.PIPE,
        stderr = subprocess.STDOUT,
        stdin = None,
        shell = True if isinstance( command, str ) else False
    )
    
    output, _ = process.communicate( )
    return process.returncode

def cat(*seqs):
    for seq in seqs:
        for item in seq:
            yield item

