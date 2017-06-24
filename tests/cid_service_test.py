
import os
import sys
import time
import signal
import stat
import pwd
import grp
import glob

import requests

from .cid_utbase import cid_UTBase
from futoin.cid.mixins.util import UtilMixIn

class cid_service_Test( cid_UTBase, UtilMixIn ) :
    __test__ = True
    
    TEST_DIR = os.path.join(cid_UTBase.TEST_RUN_DIR, 'servicecmd')
    _create_test_dir = True
    _rms_dir = os.path.join(TEST_DIR, 'rms')
    
    def test01_prepare(self):
        os.makedirs(os.path.join(self._rms_dir, 'Releases'))
        os.makedirs('src')
        os.chdir('src')
        os.mkdir('data')
        
        self._writeFile('app.sh', """#!/bin/bash
flock data -c 'echo 1>data/start.txt'
trap "flock data -c 'echo 1>data/reload.txt'" SIGHUP

# high load
while true; do
    dd if=/dev/urandom bs=64K count=1024 status=none | sha256sum >/dev/null ;
done
""")
        os.chmod('app.sh', stat.S_IRWXU)
        self._writeJSON('futoin.json', {
            'name' : 'service-test',
            'rms' : 'scp',
            'rmsRepo' : self._rms_dir,
            'rmsPool' : 'Releases',
            'persistent' : [
                'data',
            ],
            'entryPoints' : {
                'app' : {
                    'tool' : 'exe',
                    'path' : 'app.sh',
                    'tune' : {
                        'scalable': True,
                        'reloadable': True,
                        'maxInstances' : 4,
                    },
                }
            },
        })
                    
        self._call_cid(['package'])
        self._call_cid(['promote', 'Releases'] + glob.glob('*.txz'))
        
    def test02_deploy(self):
        self._call_cid(['deploy', 'rms', 'Releases', '--deployDir=dst',
                        '--rmsRepo=scp:'+self._rms_dir, '--limit-cpus=4'])
        
        deploy_conf = self._readJSON(os.path.join('dst', 'futoin.json'))
        self.assertEqual(4, len(deploy_conf['deploy']['autoServices']['app']))
        
    def test03_exec(self):
        pass