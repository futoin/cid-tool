
from .citool_utbase import citool_UTBase
import subprocess
import os


class Test_CITool_Git ( citool_UTBase ) :
    def setUpClass():
        subprocess.check_output( "rm test_git -rf && tar xf tests/test_git.tar ", shell=True )
        os.chdir( 'test_git' )
    
    def tearDownClass():
        os.chdir( '..' )
    