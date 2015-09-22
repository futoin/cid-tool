
from .citool_utbase import citool_UTBase
import subprocess


class Test_CITool_Git ( citool_UTBase ) :
    VCS_REPO = 'git:repo'
    TEST_DIR = '../test_git'

    @classmethod
    def setUpClass( cls ):
        subprocess.check_output( "rm ../test_git -rf && tar xf tests/test_git.tar -C ..", shell=True )
    