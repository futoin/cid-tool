
from __future__ import print_function
import unittest
import subprocess
import os
import sys
import stat
import shutil


CITOOL_BIN = os.path.dirname( __file__ ) + '/../bin/citool'

class citool_UTBase ( unittest.TestCase ) :
    TEST_DIR = 'invalid'
    TEST_RUN_DIR = os.path.realpath(
        os.path.join(os.path.dirname(__file__), '..', 'testrun')
    )
    __test__ = False
    _dev_null = open(os.devnull, 'w')

    @classmethod
    def setUpClass( cls ):
        try:
            os.makedirs( cls.TEST_RUN_DIR )
        except:
            pass
        
        os.chdir( cls.TEST_RUN_DIR )
        os.environ['HOME'] = cls.TEST_RUN_DIR

        if os.path.exists( cls.TEST_DIR ) :
            for ( path, dirs, files ) in os.walk( cls.TEST_DIR ) :
                for id in dirs + files :
                    os.chmod( os.path.join( path, id ), stat.S_IRWXU )
            shutil.rmtree( cls.TEST_DIR )

    def _goToBase( self ):
        os.chdir( self.TEST_DIR )

    def setUp( self ):
        self._goToBase()

    def _call_citool( self, args, stdin=None ) :
        cmd = [ sys.executable, CITOOL_BIN ] + args
        #print( 'Call: ' + subprocess.list2cmdline(cmd), file=sys.stderr )
        p = subprocess.Popen(
                cmd,
                bufsize=-1,
                stdin=subprocess.PIPE,
                stdout=self._dev_null,
                stderr=subprocess.PIPE
        )

        if stdin is not None:
            p.stdin.write( stdin )
        err = p.stderr.read()

        p.wait()
        if p.returncode != 0:
            getattr( sys.stderr, 'buffer', sys.stderr ).write( err )
            raise RuntimeError( "Failed" )
        