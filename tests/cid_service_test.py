#
# Copyright 2015-2017 Andrey Galkin <andrey@futoin.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

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

class cid_service_Test( cid_UTBase ) :
    __test__ = True
    
    TEST_DIR = os.path.join(cid_UTBase.TEST_RUN_DIR, 'servicecmd')
    _create_test_dir = True
    _rms_dir = os.path.join(TEST_DIR, 'rms')
    
    def test01_prepare(self):
        os.makedirs(os.path.join(self._rms_dir, 'Releases'))
        os.makedirs('src')
        os.chdir('src')
        os.mkdir('data')
        
        if self.IS_MACOS:
            self._writeFile('app.sh', """#!/bin/bash
                            pwd >&2
    function lock() {
        while :; do
            if mkdir data/lock; then
                break;
            fi
            
            sleep 0.1
        done
    }
    function unlock() {
        rmdir data/lock
    }
    function on_reload() {
        lock
        echo -n 1 >>data/reload.txt
        unlock
    }
    
    lock
    touch data/start.txt
    touch data/reload.txt
    echo -n "1" >>data/start.txt
    unlock
    
    trap "on_reload" SIGHUP
    trap "unlock; exit 0" SIGTERM

    # high load
    while true; do
        dd if=/dev/urandom bs=64k count=1024 2>/dev/null | shasum -a 256 >/dev/null;
    done
""")
        else:
            self._writeFile('app.sh', """#!/bin/bash
    flock data/lock -c 'echo -n "1" >>data/start.txt'
    trap "flock data/lock -c 'echo -n 1 >>data/reload.txt'" SIGHUP
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
        start_file = 'dst/persistent/data/start.txt'
        reload_file = 'dst/persistent/data/reload.txt'
        
        try: os.unlink(start_file)
        except: pass
        try: os.unlink(reload_file)
        except: pass
        
        pid1 = os.fork()
        
        if not pid1:
            self._redirectAsyncStdIO()
            
            os.execv(self.CIDTEST_BIN, [
                self.CIDTEST_BIN, 'service', 'exec', 'app', '0',
                '--deployDir=dst',
            ])
            
        pid2 = os.fork()
        
        if not pid2:
            self._redirectAsyncStdIO()
            
            os.execv(self.CIDTEST_BIN, [
                self.CIDTEST_BIN, 'service', 'exec', 'app', '3',
                '--deployDir=dst',
            ])
            
        self._call_cid(['service', 'exec', 'app', '4', '--deployDir=dst'],
                       returncode=1)
        
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
        keep_file = 'dst/persistent/data/keep.txt'
        
        self._call_cid(['deploy', 'rms', 'Releases', '--deployDir=dst',
                        '--redeploy'])
        
        self._writeFile(keep_file, 'KEEP')

        self._call_cid(['deploy', 'rms', 'Releases', '--deployDir=dst',
                        '--redeploy'])
        
        self.assertTrue(os.path.exists(keep_file))
        
    def test05_master(self):
        start_file = 'dst/persistent/data/start.txt'
        reload_file = 'dst/persistent/data/reload.txt'
        
        try: os.unlink(start_file)
        except: pass
        try: os.unlink(reload_file)
        except: pass
        
        pid = os.fork()
        
        if not pid:
            self._redirectAsyncStdIO()
            
            os.execv(self.CIDTEST_BIN, [
                self.CIDTEST_BIN, 'service', 'master',
                '--deployDir=dst',
            ])
            
        for i in range(10):
            time.sleep(1)
            
            if not os.path.exists(start_file):
                continue

            if len(self._readFile(start_file)) == 4:
                break
        else:
            self.assertTrue(False)
            
        os.kill(pid, signal.SIGUSR1)
        
        for i in range(30):
            time.sleep(1)

            if not os.path.exists(reload_file):
                continue

            if len(self._readFile(reload_file)) == 4:
                break
        else:
            self.assertTrue(False)
            
        os.kill(pid, signal.SIGTERM)
        os.waitpid(pid, 0)
        
            
