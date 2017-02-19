
from .citool_vcsutbase import citool_VCSUTBase
import subprocess
import os


class Test_CITool_Git ( citool_VCSUTBase ) :
    VCS_REPO = 'git:repo'
    TEST_DIR = os.path.join(citool_VCSUTBase.TEST_RUN_DIR, 'test_git')
