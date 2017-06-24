
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
flock data/lock -c 'echo -n "1" >>data/start.txt'
trap "flock data/lock -c 'echo -n "1" >>data/reload.txt'" SIGHUP
trap "exit 0" SIGTERM

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
        pid1 = os.fork()
        
        if not pid1:
            os.dup2(os.open(os.devnull, os.O_RDONLY), 0)
            os.dup2(os.open(os.devnull, os.O_WRONLY), 1)
            os.dup2(os.open(os.devnull, os.O_WRONLY), 2)
            
            os.execv(self.CIDTEST_BIN, [
                self.CIDTEST_BIN, 'service', 'exec', 'app', '0',
                '--deployDir=dst',
            ])
            
        pid2 = os.fork()
        
        if not pid2:
            os.dup2(os.open(os.devnull, os.O_RDONLY), 0)
            os.dup2(os.open(os.devnull, os.O_WRONLY), 1)
            os.dup2(os.open(os.devnull, os.O_WRONLY), 2)
            
            os.execv(self.CIDTEST_BIN, [
                self.CIDTEST_BIN, 'service', 'exec', 'app', '3',
                '--deployDir=dst',
            ])
            
        self._call_cid(['service', 'exec', 'app', '4', '--deployDir=dst'],
                       returncode=1)
        
        start_file = 'dst/persistent/data/start.txt'
        reload_file = 'dst/persistent/data/reload.txt'
        
        for i in range(10):
            time.sleep(1)
            
            if not os.path.exists(start_file):
                continue

            if len(self._readFile(start_file)) == 2:
                break
        else:
            self.assertTrue(False)

        self._call_cid(['service', 'reload', 'app', '4', str(pid2), '--deployDir=dst'],
                       returncode=1)
        self._call_cid(['service', 'reload', 'app', '3', str(pid2), '--deployDir=dst'])
           
        for i in range(10):
            time.sleep(1)

            if not os.path.exists(reload_file):
                continue

            if len(self._readFile(reload_file)) == 1:
                break
        else:
            self.assertTrue(False)

        self._call_cid(['service', 'stop', 'app', '4', str(pid2), '--deployDir=dst'],
                       returncode=1)
        self._call_cid(['service', 'stop', 'app', '3', str(pid2), '--deployDir=dst'])
        os.waitpid(pid2, 0)
            
        self._call_cid(['service', 'stop', 'app', '0', str(pid1), '--deployDir=dst'])
        os.waitpid(pid1, 0)

        
    def test04_redeploy(self):
        self._call_cid(['deploy', 'rms', 'Releases', '--deployDir=dst',
                        '--redeploy'])
