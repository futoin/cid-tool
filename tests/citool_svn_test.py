
from .citool_utbase import citool_UTBase
import subprocess
import os


class Test_CITool_SVN ( citool_UTBase ) :
    def setUpClass():
        subprocess.check_output( "rm test_svn -rf && tar xf tests/test_svn.tar ", shell=True )
        os.chdir( 'test_svn' )
    
    def tearDownClass():
        os.chdir( '..' )
    