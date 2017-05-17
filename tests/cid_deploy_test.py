
import os

from .cid_utbase import cid_UTBase

class cid_deploy_Test( cid_UTBase ) :
    __test__ = True
    
    TEST_DIR = os.path.join(cid_UTBase.TEST_RUN_DIR, 'deploycmd')
    
    def setUp(self):
        self.setUpClass()
        
        os.mkdir(self.TEST_DIR)
        os.chdir(self.TEST_DIR)
        
    def test_01_setup(self):
        cfg_file = os.path.join('setupdir', 'futoin.json')
        
        self._call_cid(['deploy', 'setup', '--deployDir=setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(cfg['deploy'], {})
        
        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--listen-addr=1.2.3.4'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(cfg['deploy'], {
            'listenAddress': '1.2.3.4',
        })
        
        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--limit-cpus=3'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(cfg['deploy'], {
            'maxCpuCount': 3,
            'listenAddress': '1.2.3.4',
        })
        
        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--limit-memory=18M'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(cfg['deploy'], {
            'maxTotalMemory' : '18M',
            'maxCpuCount': 3,
            'listenAddress': '1.2.3.4',
        })

