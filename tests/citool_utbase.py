
from __future__ import print_function
import unittest
import subprocess
import os
import sys


CITOOL_BIN = os.path.dirname( __file__ ) + '/../bin/citool'

class citool_UTBase ( unittest.TestCase ) :
    TEST_DIR = 'invalid'
    TEST_RUN_DIR = os.path.realpath(
        os.path.join(os.path.dirname(__file__), '..', 'testrun')
    )

    @classmethod
    def setUpClass( cls ):
        try:
            os.makedirs( cls.TEST_RUN_DIR )
        except:
            pass
        
        os.chdir( cls.TEST_RUN_DIR )

        if os.path.exists( cls.TEST_DIR ) :
            for r, dirs, files in os.walk( cls.TEST_DIR, False ):  
                for f in dirs + files:
                    f = os.path.join(r, f)
                    os.chmod(f, stat.S_IRWXU)
            for r, dirs, files in os.walk( cls.TEST_DIR, False ):  
                for d in dirs:
                    os.rmdir(os.path.join(r, d))
                for f in files:
                    os.remove(os.path.join(r, f))
            os.rmdir( cls.TEST_DIR )

    def _goToBase( self ):
        os.chdir( self.TEST_DIR )

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
        