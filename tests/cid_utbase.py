
from __future__ import print_function, absolute_import
import unittest
import subprocess
import os
import sys
import stat
import shutil
import json
from collections import OrderedDict

CIDTEST_BIN = os.environ.get('CIDTEST_BIN', None)

if CIDTEST_BIN:
    CIDTEST_BIN_EXT = False
else :
    CIDTEST_BIN_EXT = True
    CIDTEST_BIN = os.path.dirname( __file__ ) + '/../bin/cid'

class cid_UTBase ( unittest.TestCase ) :
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
    def _call_cid( cls, args, stdin=None, stdout=None, returncode=0, ignore=False, retout=False ) :
        cmd = []
        
        if CIDTEST_BIN_EXT:
            cmd.append(sys.executable)
            
        if retout:
            (r, w) = os.pipe()
            stdout = w
            
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
        
        if retout:
            res = os.read(r, 4096)
            os.close(r)
            os.close(w)
        
        if ignore:
            return
        
        if p.returncode != returncode:
            getattr( sys.stderr, 'buffer', sys.stderr ).write( err )
            raise RuntimeError( "Failed" )
        
        if retout:
            try: res = str(res, 'utf8')
            except: pass
        
            return res
        
    @classmethod
    def _writeFile( cls, file_name, content ):
        with open(file_name, 'w') as content_file:
            content_file.write( content )
            content_file.write( "\n" )

    @classmethod
    def _writeJSON( cls, file_name, content ):
        cls._writeFile( file_name, json.dumps( content ) )
        
    @classmethod
    def _readFile( cls, file_name ):
        with open(file_name, 'r') as content_file:
            content = content_file.read()
            return content
        
    @classmethod
    def _readJSON( cls, file_name ):
        content = cls._readFile(file_name)
        object_pairs_hook = lambda pairs: OrderedDict( pairs )
        return json.loads( content, object_pairs_hook=object_pairs_hook )
        
class cid_Tool_UTBase ( cid_UTBase ) :
    __test__ = False
    TOOL_NAME = 'invalid'
    TOOL_ENV = {}
    _env_backup = None

    @classmethod
    def setUpClass( cls ):
        cls._env_backup = {}
        cls.TEST_DIR = os.path.join(cls.TEST_RUN_DIR, 'tool_'+cls.TOOL_NAME)
        super(cid_Tool_UTBase, cls).setUpClass()
        os.mkdir( cls.TEST_DIR )
        os.chdir( cls.TEST_DIR )
        
        for k, v in cls.TOOL_ENV.items():
            cls._env_backup[k] = os.environ.get(k, None)
            os.environ[k] = v
            
    @classmethod
    def tearDownClass( cls ):
        for k, v in cls._env_backup.items():
            if v:
                os.environ[k] = v
            else:
                del os.environ[k]