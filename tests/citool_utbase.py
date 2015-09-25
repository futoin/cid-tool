
from __future__ import print_function
import unittest
import subprocess
import os
import sys
from citool.subtool import SubTool


CITOOL_BIN = os.path.dirname( __file__ ) + '/../bin/citool'

class citool_UTBase ( unittest.TestCase ) :
    def _goToBase( self ):
        os.chdir( os.path.dirname( __file__ ) + '/../' + self.TEST_DIR )

    def setUp( self ):
        self._goToBase()

    def _call_citool( self, args, stdin=None ) :
        #print( [ CITOOL_BIN ] + args, file=sys.stderr )
        p = subprocess.Popen(
                [ CITOOL_BIN ] + args,
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
        
    def test_tag( self ):
        self._call_citool( [ 'tag', 'branch_A', '--vcsRepo', self.VCS_REPO ] )
        
    def test_tag_ver( self ):
        self._call_citool( [
            'tag', 'branch_A', '1.3.0',
            '--vcsRepo', self.VCS_REPO,
            '--wcDir', 'build_ver' ] )
        
    def test_prepare( self ):
        self._call_citool( [ 'prepare', 'branch_A', '--vcsRepo', self.VCS_REPO, '--wcDir', 'prep_dir' ] )
        self._goToBase()
        self._call_citool( [ 'prepare', 'v1.2.3', '--wcDir', 'prep_dir' ] )
        self._goToBase()
        os.chdir( 'prep_dir' )
        self._call_citool( [ 'prepare', 'branch_A' ] )
    
    def test_ci_build( self ):
        try:
            os.makedirs( 'rms_repo/Builds')
            os.makedirs( 'rms_repo/Verified')
            os.makedirs( 'rms_repo/Prod')
        except :
            pass
        
        rms_dir = os.path.realpath( 'rms_repo' )

        self._call_citool( [ 'ci_build', 'branch_A', 'Builds',
                            '--vcsRepo', self.VCS_REPO,
                            '--rmsRepo', 'scp:' + rms_dir ] )
        
        self._goToBase()
        os.chdir( 'build' )
        package = subprocess.check_output( 'cd %s && ls Builds/*.tar.* | head -1' % rms_dir, shell=True )
        try:
            package = str(package, 'utf8').strip()
        except TypeError:
            package = str(package).strip()
            
        package_base = os.path.basename( package )
        pkg_hash = SubTool.rmsCalcHash( package_base, 'sha512' )
        os.unlink( package_base )
        self._call_citool( [ 'promote', package, 'Verified',
                            '--rmsRepo', 'scp:' + rms_dir,
                            '--rmsHash', pkg_hash ] )
        
        self._goToBase()
        os.chdir( 'build' )
        self._call_citool( [ 'promote', package, 'Prod',
                            '--rmsRepo', 'scp:' + rms_dir,
                            '--rmsHash', pkg_hash ] )
        