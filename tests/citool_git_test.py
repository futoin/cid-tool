
from .citool_utbase import citool_UTBase
import subprocess
import os


class Test_CITool_Git ( citool_UTBase ) :
    VCS_REPO = 'git:repo'
    @classmethod
    def setUpClass( cls ):
        subprocess.check_output( "rm test_git -rf && tar xf tests/test_git.tar ", shell=True )
        os.chdir( 'test_git' )
        
    @classmethod
    def tearDownClass( cls ):
        os.chdir( '..' )
    