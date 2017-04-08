
from __future__ import print_function, absolute_import

from .citool_utbase import citool_UTBase
from futoin.cid.rmstool import RmsTool

import os, stat
import subprocess
import glob

from collections import OrderedDict

class cid_misc_Test ( citool_UTBase ) :
    __test__ = True
    TEST_DIR = os.path.join(citool_UTBase.TEST_RUN_DIR, 'misc')
    ORIG_HOME = os.environ['HOME']
    
    def setUp(self):
        self.setUpClass()
        
        os.mkdir(self.TEST_DIR)
        os.chdir(self.TEST_DIR)
        
        subprocess.check_call('sudo mkdir -p /etc/futoin && sudo chmod 777 /etc/futoin', shell=True)
        
        home = os.path.join(self.TEST_DIR, 'home')
        os.mkdir(home)
        os.environ['HOME'] = home
        
    def tearDown(self):
        os.environ['HOME'] = self.ORIG_HOME
        subprocess.call('sudo rm /etc/futoin -rf', shell=True)
            
    def test_global_config(self):
        self._writeJSON('/etc/futoin/futoin.json', {
            'env' : {}
        })
        self._call_citool(['tool', 'list'])
        
        
        self._writeJSON('/etc/futoin/futoin.json', {
            'invalid' : {}
        })
        
        self._call_citool(['tool', 'list'], returncode=1)

    def test_user_config_notdot(self):
        self._writeJSON(os.path.join(os.environ['HOME'], 'futoin.json'), {
            'env' : {}
        })
        self._call_citool(['tool', 'list'])
        
        
        self._writeJSON(os.path.join(os.environ['HOME'], 'futoin.json'), {
            'invalid' : {}
        })
        
        self._call_citool(['tool', 'list'], returncode=1)

    def test_user_dot_config(self):
        self._writeJSON(os.path.join(os.environ['HOME'], '.futoin.json'), {
            'env' : {}
        })
        self._call_citool(['tool', 'list'])
        
        
        self._writeJSON(os.path.join(os.environ['HOME'], '.futoin.json'), {
            'invalid' : {}
        })
        
        self._call_citool(['tool', 'list'], returncode=1)

    def test_unknown_tool(self):
        self._writeJSON(os.path.join(self.TEST_DIR, 'futoin.json'), {
            'tools' : {
                'unknown_tool' : True,
            }
        })
        self._call_citool(['tool', 'list'], returncode=1)


