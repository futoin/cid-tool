
from .citool_vcsutbase import citool_VCSUTBase
import subprocess
import os


class Test_CITool_Hg ( citool_VCSUTBase ) :
    VCS_REPO = 'hg:repo'
    TEST_DIR = '../test_hg'

    @classmethod
    def setUpClass( cls ):
        os.chdir( os.path.dirname( __file__ ) + '/..' )
        cls.VCS_REPO = 'hg:' + os.path.realpath( '../test_hg/repo' )
        subprocess.check_output( "chmod -R ug+w ../test_hg; rm ../test_hg -rf && tar xf tests/test_hg.tar -C ..", shell=True )
    