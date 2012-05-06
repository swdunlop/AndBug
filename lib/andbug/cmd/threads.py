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

'implementation of the "threads" command'

import andbug.command, andbug.screed
import re

def thread_methods(t, verbose):
    for f in t.frames:
        name = str(f.loc)
        if f.native:
            name += ' <native>'
        with andbug.screed.item(name):
            if verbose > 1:
                for k, v in f.values.items():
                    if verbose == 2:
                        andbug.screed.item("%s=<%s>" % (k, type(v).__name__))
                    else:
                        andbug.screed.item("%s=%s <%s>" % (k, v, type(v).__name__))
 
@andbug.command.action('[<name>] [verbose=<verbose level>]')
def threads(ctxt, arg1 = None, arg2 = None):
    'lists threads in the process. verbosity: 0 (thread), (1 methods), (2 vars), (3 vars data)'

    def threadId(name):
        """Extract threadId from name (e.g. "thread <2> HeapWorker" => 2)."""
        return int(re.split('<|>', str(name))[1])

    def parse_verbosity(param):
        """Return False if it's not a verbosity argument.
        If it's an invalid number return 0"""
        if param is None or param[:8] != 'verbose=':
            return False

        verbosity = int(param[8:])
        return verbosity

    def parse_args(arg1, arg2):
        if arg1 is None:
            return (None, 0)

        if arg2 is None:
            verbose = parse_verbosity(arg1)
            if verbose is False:
                return (arg1, 0)
            else:
                return (None, verbose)

        verbose = parse_verbosity(arg2)
        if verbose is False: verbose = 0
        
        return (arg1, verbose)

    name, verbose = parse_args(arg1, arg2)
    ctxt.sess.suspend()

    try:
        threads = sorted(ctxt.sess.threads(name).items, key=threadId)

        for t in threads:
            with andbug.screed.section(str(t)):
                if verbose > 0:
                    thread_methods(t, verbose)
    finally:
        ctxt.sess.resume()
        
