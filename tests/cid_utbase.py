
from __future__ import print_function, absolute_import
import unittest
import subprocess
import os
import sys
import stat
import shutil
import json
import platform
from collections import OrderedDict
from futoin.cid.util import executil

CIDTEST_BIN = os.environ.get('CIDTEST_BIN', None)

if CIDTEST_BIN:
    CIDTEST_BIN_EXT = False
else :
    CIDTEST_BIN_EXT = True
    CIDTEST_BIN = os.path.dirname( __file__ ) + '/../bin/cid'

class cid_UTBase ( unittest.TestCase ) :
    IS_LINUX = platform.system() == 'Linux'
    IS_MACOS = platform.system() == 'Darwin'
    NO_COMPILE = os.environ.get('CIDTEST_NO_COMPILE', '0') == '1'
    ALLOW_SRC_BUILDS = not NO_COMPILE
    
    CIDTEST_BIN = CIDTEST_BIN
    TEST_DIR = 'invalid'
    TEST_RUN_DIR = os.environ.get('CIDTEST_RUN_DIR', os.path.realpath(
        os.path.join(os.path.dirname(__file__), '..', 'testrun')
    ))
    _create_test_dir = False
    __test__ = False
    _dev_null = open(os.devnull, 'w')
    _stdout_log = open(os.path.join(TEST_RUN_DIR, 'stdout.log'), 'a+')
    #_stderr_log = open(os.path.join(TEST_RUN_DIR, 'stderr.log'), 'a+')
    _stderr_log = _stdout_log

    @classmethod
    def setUpClass( cls ):
        print('Python: ' + sys.executable)
        try:
            os.makedirs( cls.TEST_RUN_DIR )
        except:
            pass
        
        os.chdir( cls.TEST_RUN_DIR )
        os.environ['HOME'] = cls.TEST_RUN_DIR

        cache_dir = os.path.join(os.environ['HOME'], '.cache', 'futoin-cid')

        for cleanup_dir in (cache_dir, cls.TEST_DIR):
            if os.path.exists( cleanup_dir ) :
                for ( path, dirs, files ) in os.walk( cleanup_dir ) :
                    for id in dirs + files :
                        try:
                            os.chmod( os.path.join( path, id ), stat.S_IRWXU )
                        except:
                            pass
                shutil.rmtree( cleanup_dir )
                
        if cls._create_test_dir:
            os.mkdir(cls.TEST_DIR)
            os.chdir(cls.TEST_DIR)            
            
    def _goToBase( self ):
        os.chdir( self.TEST_DIR )

    def setUp( self ):
        self._goToBase()

    @classmethod
    def _call_cid( cls, args, stdin=None, stdout=None, returncode=0, ignore=False, retout=False, merge_stderr=False ) :
        cmd = []
        
        if CIDTEST_BIN_EXT:
            cmd.append(sys.executable)
            
        if retout:
            (r, w) = os.pipe()
            stdout = w
            
        cmd.append( CIDTEST_BIN )
        cmd += args
        
        if stdout is None:
            stdout = cls._stdout_log
            
        stderr = cls._stderr_log
        
        if merge_stderr:
            stderr=subprocess.STDOUT
        
        print( 'Test Call: ' + subprocess.list2cmdline(cmd), file=cls._stderr_log )
        cls._stderr_log.flush()

        p = subprocess.Popen(
                cmd,
                bufsize=-1,
                stdin=subprocess.PIPE,
                stdout=stdout,
                stderr=stderr
        )

        if stdin is not None:
            p.stdin.write( stdin )

        p.wait()
        
        if retout:
            os.close(w)
            res = os.read(r, 32*1024)
            os.close(r)
        
        if ignore:
            return p.returncode == returncode
        
        if p.returncode != returncode:
            raise RuntimeError( "Failed" )
        
        if retout:
            return executil.toString(res)
        
        return True
        
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
    
    @classmethod
    def _redirectAsyncStdIO( cls ):
        os.dup2(cls._dev_null.fileno(), 0)
        os.dup2(cls._stdout_log.fileno(), 1)
        os.dup2(cls._stderr_log.fileno(), 2)
        
    def _firstGet(self, url):
        import requests, time

        for i in range(15):
            try:
                res = requests.get(url, timeout=3)
                
                if res.ok:
                    return res
                else:
                    time.sleep(1)
            except:
                time.sleep(1)
        else:
            self.assertTrue(False)
        
        
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