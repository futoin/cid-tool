
from .citool_utbase import citool_UTBase
import subprocess
import os


class Test_CITool_Hg ( citool_UTBase ) :
    VCS_REPO = 'hg:repo'
    TEST_DIR = '../test_hg'

    @classmethod
    def setUpClass( cls ):
        os.chdir( os.path.dirname( __file__ ) + '/..' )
        cls.VCS_REPO = 'hg:' + os.path.realpath( '../test_hg/repo' )
        subprocess.check_output( "rm ../test_hg -rf && tar xf tests/test_hg.tar -C ..", shell=True )
    