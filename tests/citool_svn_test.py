
from .citool_vcsutbase import citool_VCSUTBase
import subprocess
import os


class Test_CITool_SVN ( citool_VCSUTBase ) :
    __test__ = True
    TEST_DIR = os.path.join(citool_VCSUTBase.TEST_RUN_DIR, 'test_svn')
    VCS_REPO = 'svn:file://' + os.path.join( TEST_DIR, 'repo' )
