
from .citool_vcsutbase import citool_VCSUTBase
import subprocess
import os


class Test_CITool_Git ( citool_VCSUTBase ) :
    VCS_REPO = 'git:repo'
    TEST_DIR = '../test_git'

    @classmethod
    def setUpClass( cls ):
        os.chdir( os.path.dirname( __file__ ) + '/..' )
        subprocess.check_output( "chmod -R ug+w ../test_git; rm ../test_git -rf && tar xf tests/test_git.tar -C ..", shell=True )
    