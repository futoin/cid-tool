
from __future__ import print_function, absolute_import

from .citool_utbase import citool_UTBase
from futoin.cid.rmstool import RmsTool

import os, stat
import subprocess
import glob

from collections import OrderedDict

class cid_initcmd_Test ( citool_UTBase ) :
    __test__ = True
    TEST_DIR = os.path.join(citool_UTBase.TEST_RUN_DIR, 'misc')
    
    def setUp(self):
        self.setUpClass()
        
        os.mkdir(self.TEST_DIR)
        os.chdir(self.TEST_DIR)
        
        subprocess.check_call('sudo mkdir -p /etc/futoin && chmod 777 /etc/futoin', shell=True)
        
    def tearDown(self):
        subprocess.call('sudo rm /etc/futoin -rf', shell=True)
            
    def check_global_config(self):
        self._writeJSON('/etc/futoin/futoin.json', {
            'env' : {}
        })
        self._call_citool(['tool', 'list'])
        
        
        self._writeJSON('/etc/futoin/futoin.json', {
            'invalid' : {}
        })
        
        self._call_citool(['tool', 'list'], returncode=1)

    def check_user_config_notdot(self):
        self._writeJSON(os.path.join(os.environ['HOME'], 'futoin.json'), {
            'env' : {}
        })
        self._call_citool(['tool', 'list'])
        
        
        self._writeJSON(os.path.join(os.environ['HOME'], 'futoin.json'), {
            'invalid' : {}
        })
        
        self._call_citool(['tool', 'list'], returncode=1)

    def check_user_dot_config(self):
        self._writeJSON(os.path.join(os.environ['HOME'], '.futoin.json'), {
            'env' : {}
        })
        self._call_citool(['tool', 'list'])
        
        
        self._writeJSON(os.path.join(os.environ['HOME'], '.futoin.json'), {
            'invalid' : {}
        })
        
        self._call_citool(['tool', 'list'], returncode=1)

