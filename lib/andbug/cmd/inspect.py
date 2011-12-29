## Copyright 2011, Felipe Barriga Richards <spam@felipebarriga.cl>.
##                 All rights reserved.
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

'implementation of the "inspect" command'

import andbug.command, andbug.screed

def find_object(ctxt, oid):
    for t in ctxt.sess.threads():
        for f in t.frames:
            for k, v in f.values.items():
                if type(v) is andbug.vm.Object and v.oid == oid:
                    return (v, t)
    return None

@andbug.command.action('<object-id>')
def inspect(ctxt, oid):
    'inspect an object'
    ctxt.sess.suspend()
    
    try:
        oid = long(oid)
        rtval = find_object(ctxt, oid)
        if rtval is None:
            andbug.screed.section('object <%s> not found' % oid)
        else:
            obj, thread = rtval
            with andbug.screed.section('object <%s> %s in %s'
                % (str(obj.oid), str(obj.jni), str(thread))):
                for k, v in obj.fields.items():
                    andbug.screed.item('%s=%s <%s>' % (k, v, type(v).__name__))
    except ValueError:
        print('!! error, invalid oid param. expecting <long> and got <%s>.'
            % type(oid).__name__)

    finally:
        ctxt.sess.resume()
  