
from .citool_utbase import citool_UTBase
import subprocess
import os


class Test_CITool_SVN ( citool_UTBase ) :
    VCS_REPO = 'svn:file//repo'
    TEST_DIR = '../test_svn'

    @classmethod
    def setUpClass( cls ):
        subprocess.check_output( "rm ../test_svn -rf && tar xf tests/test_svn.tar -C ..", shell=True )
    