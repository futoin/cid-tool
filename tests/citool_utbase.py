
from __future__ import print_function, absolute_import
import unittest
import subprocess
import os
import sys
import stat
import shutil
import json

CIDTEST_BIN = os.environ.get('CIDTEST_BIN', None)

if CIDTEST_BIN:
    CIDTEST_BIN_EXT = False
else :
    CIDTEST_BIN_EXT = True
    CIDTEST_BIN = os.path.dirname( __file__ ) + '/../bin/cid'

class citool_UTBase ( unittest.TestCase ) :
    TEST_DIR = 'invalid'
    TEST_RUN_DIR = os.environ.get('CIDTEST_RUN_DIR', os.path.realpath(
        os.path.join(os.path.dirname(__file__), '..', 'testrun')
    ))
    __test__ = False
    _dev_null = open(os.devnull, 'w')

    @classmethod
    def setUpClass( cls ):
        print('Python: ' + sys.executable)
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

    @classmethod
    def _call_citool( cls, args, stdin=None, stdout=None, returncode=0 ) :
        cmd = []
        
        if CIDTEST_BIN_EXT:
            cmd.append(sys.executable)
            
        cmd.append( CIDTEST_BIN )
        cmd += args
        
        if stdout is None:
            stdout = cls._dev_null
        
        #print( 'Call: ' + subprocess.list2cmdline(cmd), file=sys.stderr )
        p = subprocess.Popen(
                cmd,
                bufsize=-1,
                stdin=subprocess.PIPE,
                stdout=stdout,
                stderr=subprocess.PIPE
        )

        if stdin is not None:
            p.stdin.write( stdin )
        err = p.stderr.read()

        p.wait()
        if p.returncode != returncode:
            getattr( sys.stderr, 'buffer', sys.stderr ).write( err )
            raise RuntimeError( "Failed" )
        
    @classmethod
    def _writeFile( cls, file_name, content ):
        with open(file_name, 'w') as content_file:
            content_file.write( content )
            content_file.write( "\n" )

    @classmethod
    def _writeJSON( cls, file_name, content ):
        cls._writeFile( file_name, json.dumps( content ) )
        