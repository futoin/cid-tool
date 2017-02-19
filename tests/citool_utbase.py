
from __future__ import print_function
import unittest
import subprocess
import os
import sys


CITOOL_BIN = os.path.dirname( __file__ ) + '/../bin/citool'

class citool_UTBase ( unittest.TestCase ) :
    def _goToBase( self ):
        os.chdir( os.path.dirname( __file__ ) + '/../' + self.TEST_DIR )

    def setUp( self ):
        self._goToBase()

    def _call_citool( self, args, stdin=None ) :
        cmd = [ sys.executable, CITOOL_BIN ] + args
        #print( ' '.join(cmd), file=sys.stderr )
        p = subprocess.Popen(
                cmd,
                bufsize=-1,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
        )

        if stdin is not None:
            p.stdin.write( stdin )
        p.stdout.read()
        err = p.stderr.read()

        p.wait()
        if p.returncode != 0:
            getattr( sys.stderr, 'buffer', sys.stderr ).write( err )
            raise RuntimeError( "Failed" )
        