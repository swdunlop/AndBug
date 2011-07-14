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

from andbug.options import parse_cpath, parse_mquery
from unittest import TestCase, main as test_main

class TestOptions(TestCase):
    def test_cpath(self):
        def case(opt, res):
            self.assertEqual(parse_cpath(opt), res)
        
        case('a.b.c.d', 'La/b/c/d;')
        case('La/b/c/d;', 'La/b/c/d;')
        case('La;', 'La;')
        case('a', 'La;')
    
    def test_mquery(self):
        def case(c, m, (cp, mn, mj)):
            p, n, j = parse_mquery(c, m)
            self.assertEqual(cp, p)
            self.assertEqual(mn, n)
            self.assertEqual(mj, j)
 
        case('abc',       None,       ('Labc;', None, None))
        case('abc',       '',         ('Labc;', None, None))
        case('abc',       '*',        ('Labc;', None, None))
        case('abc',       'foo',      ('Labc;', 'foo', None))
        case('abc.xyz',   'foo()I',   ('Labc/xyz;', 'foo', '()I'))
        case('Labc/xyz;', 'foo(DD)I', ('Labc/xyz;', 'foo', '(DD)I'))
        
if __name__ == '__main__':
    test_main()