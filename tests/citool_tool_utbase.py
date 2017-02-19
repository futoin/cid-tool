
from .citool_utbase import citool_UTBase
import os

class citool_Tool_UTBase ( citool_UTBase ) :
    TOOL_NAME = 'invalid'

    @classmethod
    def setUpClass( cls ):
        cls.TEST_DIR = os.path.join(cls.TEST_RUN_DIR, 'tool_'+cls.TOOL_NAME)
        super(citool_Tool_UTBase, cls).setUpClass()
        os.mkdir( cls.TEST_DIR )
        os.chdir( cls.TEST_DIR )
