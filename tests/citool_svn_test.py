
from .citool_vcsutbase import citool_VCSUTBase
import subprocess
import os


class Test_CITool_SVN ( citool_VCSUTBase ) :
    VCS_REPO = 'svn:file//repo'
    TEST_DIR = '../test_svn'

    @classmethod
    def setUpClass( cls ):
        os.chdir( os.path.dirname( __file__ ) + '/..' )
        cls.VCS_REPO = 'svn:file://' + os.path.realpath( cls.TEST_DIR + '/repo' )
        subprocess.check_output( "chmod -R ug+w ../test_svn; rm ../test_svn -rf && tar xf tests/test_svn.tar -C ..", shell=True )
    