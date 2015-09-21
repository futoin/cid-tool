
import unittest
import subprocess
import os

CITOOL_BIN = os.path.dirname( __file__ ) + '/../bin/citool'

class citool_UTBase ( unittest.TestCase ) :
    def _call_citool( self, args ) :
        subprocess.check_output( [ CITOOL_BIN ] + args )
        
    def test_tag( self ):
        self._call_citool( [ 'tag', 'branch_A', '--vcsRepo', self.VCS_REPO ] )
    