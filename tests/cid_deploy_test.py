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
from nose.plugins.attrib import attr

import requests

from .cid_utbase import cid_UTBase
from futoin.cid.details.resourcealgo import ResourceAlgo
from futoin.cid.util import executil as _executil
from futoin.cid.util import configutil as _configutil

class cid_deploy_Test( cid_UTBase ) :
    __test__ = True
    
    TEST_DIR = os.path.join(cid_UTBase.TEST_RUN_DIR, 'deploycmd')
    _create_test_dir = True
        
    def test_01_setup(self):
        cfg_file = os.path.join('setupdir', 'futoin.json')
        
        runtime_dir = os.path.join(self.TEST_DIR, 'setupdir', '.runtime')
        tmp_dir = os.path.join(self.TEST_DIR, 'setupdir', '.tmp')
        
        user = pwd.getpwuid(os.geteuid())[0]
        group = grp.getgrgid(os.getegid())[0]
        
        self._call_cid(['deploy', 'setup', '--deployDir=setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(dict(cfg['deploy']), {
            'runtimeDir' : runtime_dir,
            'tmpDir' : tmp_dir,
            'autoServices': {},
            'user' : user,
            'group' : group,
        })
        
        self._call_cid(['deploy', 'setup', '--deployDir=setupdir', '--runtimeDir=/tmp/someother'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(dict(cfg['deploy']), {
            'autoServices': {},
            'runtimeDir' : '/tmp/someother',
            'tmpDir' : tmp_dir,
            'user' : user,
            'group' : group,
        })

        self._call_cid(['deploy', 'setup', '--deployDir=setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(dict(cfg['deploy']), {
            'autoServices': {},
            'runtimeDir' : '/tmp/someother',
            'tmpDir' : tmp_dir,
            'user' : user,
            'group' : group,
        })

        self._call_cid(['deploy', 'setup', '--deployDir=setupdir', '--runtimeDir=auto'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(dict(cfg['deploy']), {
            'runtimeDir' : runtime_dir,
            'tmpDir' : tmp_dir,
            'autoServices': {},
            'user' : user,
            'group' : group,
        })
        
        
        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--listen-addr=1.2.3.4'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(dict(cfg['deploy']), {
            'runtimeDir' : runtime_dir,
            'tmpDir' : tmp_dir,
            'autoServices': {},
            'listenAddress': '1.2.3.4',
            'user' : user,
            'group' : group,
        })
        
        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--limit-cpus=3'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(dict(cfg['deploy']), {
            'runtimeDir' : runtime_dir,
            'tmpDir' : tmp_dir,
            'autoServices': {},
            'maxCpuCount': 3,
            'listenAddress': '1.2.3.4',
            'user' : user,
            'group' : group,
        })
        
        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--limit-memory=18M'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(dict(cfg['deploy']), {
            'runtimeDir' : runtime_dir,
            'tmpDir' : tmp_dir,
            'autoServices': {},
            'maxTotalMemory' : '18M',
            'maxCpuCount': 3,
            'listenAddress': '1.2.3.4',
            'user' : user,
            'group' : group,
        })

        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--limit-memory=auto'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(dict(cfg['deploy']), {
            'runtimeDir' : runtime_dir,
            'tmpDir' : tmp_dir,
            'autoServices': {},
            'maxCpuCount': 3,
            'listenAddress': '1.2.3.4',
            'user' : user,
            'group' : group,
        })

        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--limit-cpus=auto'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(dict(cfg['deploy']), {
            'runtimeDir' : runtime_dir,
            'tmpDir' : tmp_dir,
            'autoServices': {},
            'listenAddress': '1.2.3.4',
            'user' : user,
            'group' : group,
        })
        
        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--user=someuser',
                        '--group=somegroup'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(dict(cfg['deploy']), {
            'runtimeDir' : runtime_dir,
            'tmpDir' : tmp_dir,
            'autoServices': {},
            'listenAddress': '1.2.3.4',
            'user' : 'someuser',
            'group' : 'somegroup',
        })
        
        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(dict(cfg['deploy']), {
            'runtimeDir' : runtime_dir,
            'tmpDir' : tmp_dir,
            'autoServices': {},
            'listenAddress': '1.2.3.4',
            'user' : 'someuser',
            'group' : 'somegroup',
        })
        
        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--user=auto',
                        '--group=auto'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(dict(cfg['deploy']), {
            'runtimeDir' : runtime_dir,
            'tmpDir' : tmp_dir,
            'autoServices': {},
            'listenAddress': '1.2.3.4',
            'user' : user,
            'group' : group,
        })
        
        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--tmpDir=/other/tmp'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(dict(cfg['deploy']), {
            'runtimeDir' : runtime_dir,
            'tmpDir' : tmp_dir,
            'tmpDir' : '/other/tmp',
            'autoServices': {},
            'listenAddress': '1.2.3.4',
            'user' : user,
            'group' : group,
        })

        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--tmpDir=auto'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(dict(cfg['deploy']), {
            'runtimeDir' : runtime_dir,
            'tmpDir' : tmp_dir,
            'autoServices': {},
            'listenAddress': '1.2.3.4',
            'user' : user,
            'group' : group,
        })
        
    def test_08_set_persistent(self):
        cfg_file = os.path.join('setupdir', 'futoin.json')
        
        self._call_cid(['deploy', 'set', 'persistent',
                        'path1', 'path/2',
                        '--deployDir', 'setupdir',
                        ])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(
            sorted([
                'path1',                
                'path/2',
            ]),
            cfg['persistent'])

        self._call_cid(['deploy', 'set', 'persistent',
                        'path/2', 'path/3/a',
                        '--deployDir', 'setupdir'
                        ])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(
            sorted([
                'path1',
                'path/2',
                'path/3/a',
            ]),
            cfg['persistent'])
            
    def test_09_set_writable(self):
        cfg_file = os.path.join('setupdir', 'futoin.json')
        
        self._call_cid(['deploy', 'set', 'writable',
                        'wpath1', 'wpath/2',
                        '--deployDir', 'setupdir',
                        ])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(
            sorted([
                'wpath1',                
                'wpath/2',
            ]),
            cfg['writable'])

        self._call_cid(['deploy', 'set', 'writable',
                        'wpath/2', 'wpath/3/a',
                        '--deployDir', 'setupdir'
                        ])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(
            sorted([
                'wpath1',
                'wpath/2',
                'wpath/3/a',
            ]),
            cfg['writable'])
            
    def test_09_set_env(self):
        cfg_file = os.path.join('setupdir', 'futoin.json')
        
        self._call_cid(['deploy', 'set', 'env', 'myVar', '3', '--deployDir', 'setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals('3', cfg['env']['myVar'])

        self._call_cid(['deploy', 'set', 'env', 'myVar', '456', '--deployDir', 'setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals('456', cfg['env']['myVar'])

        self._call_cid(['deploy', 'set', 'env', 'myVar','--deployDir', 'setupdir' ])
        cfg = self._readJSON(cfg_file)
        self.assertTrue('myVar' not in cfg['env'])
        
    def test_10_set_webcfg(self):
        cfg_file = os.path.join('setupdir', 'futoin.json')
        
        self._call_cid(['deploy', 'set', 'webcfg', 'root', '/webroot', '--deployDir', 'setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals('/webroot', cfg['webcfg']['root'])

        self._call_cid(['deploy', 'set', 'webcfg', 'root', '--deployDir', 'setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertTrue('root' not in cfg['webcfg'])
        
        self._call_cid(['deploy', 'set', 'webcfg', 'mounts', '/admin=myapp', '--deployDir', 'setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals('myapp', cfg['webcfg']['mounts']['/admin'])

        self._call_cid(['deploy', 'set', 'webcfg', 'mounts', '/admin2=myapp2', '--deployDir', 'setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals('myapp', cfg['webcfg']['mounts']['/admin'])
        self.assertEquals('myapp2', cfg['webcfg']['mounts']['/admin2'])

        self._call_cid(['deploy', 'set', 'webcfg', 'mounts', '/admin2=', '--deployDir', 'setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals('myapp', cfg['webcfg']['mounts']['/admin'])
        self.assertTrue('/admin2' not in cfg['webcfg']['mounts'])
        
        self._call_cid(['deploy', 'set', 'webcfg', 'mounts', '/admin=', '--deployDir', 'setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertTrue('/admin' not in cfg['webcfg']['mounts'])
        self.assertTrue('/admin2' not in cfg['webcfg']['mounts'])
        
    def test_11_set_entrypoint(self):
        cfg_file = os.path.join('setupdir', 'futoin.json')
        
        self._call_cid(['deploy', 'set', 'entrypoint', 'app', 'exe', 'file.exe', '--deployDir', 'setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals({
                'app': {
                    'tool' : 'exe',
                    'path' : 'file.exe',
                    'tune' : {},
                },
            },
            dict(cfg['entryPoints']))
            
        self._call_cid(['deploy', 'set', 'entrypoint', 'app2', 'exe', 'file2.exe', '--deployDir', 'setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals({
                'app': {
                    'tool' : 'exe',
                    'path' : 'file.exe',
                    'tune' : {},
                },
                'app2': {
                    'tool' : 'exe',
                    'path' : 'file2.exe',
                    'tune' : {},
                },
            },
            dict(cfg['entryPoints']))

        self._call_cid(['deploy', 'set', 'entrypoint', 'app2', 'exe', 'file2.exe', 'myTune=123', '--deployDir', 'setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals({
                'app': {
                    'tool' : 'exe',
                    'path' : 'file.exe',
                    'tune' : {},
                },
                'app2': {
                    'tool' : 'exe',
                    'path' : 'file2.exe',
                    'tune' : {
                        'myTune' : '123',
                    },
                },
            },
            dict(cfg['entryPoints']))
        
        self._call_cid(['deploy', 'set', 'entrypoint', 'app2', 'exe', 'file2.exe', 'myTune2=some', '--deployDir', 'setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals({
                'app': {
                    'tool' : 'exe',
                    'path' : 'file.exe',
                    'tune' : {},
                },
                'app2': {
                    'tool' : 'exe',
                    'path' : 'file2.exe',
                    'tune' : {
                        'myTune' : '123',
                        'myTune2' : 'some',
                    },
                },
            },
            dict(cfg['entryPoints']))
                    
        self._call_cid(['deploy', 'set', 'entrypoint', 'app2', 'exe', 'file2.exe', 'myTune2=', '--deployDir', 'setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals({
                'app': {
                    'tool' : 'exe',
                    'path' : 'file.exe',
                    'tune' : {},
                },
                'app2': {
                    'tool' : 'exe',
                    'path' : 'file2.exe',
                    'tune' : {
                        'myTune' : '123',
                    },
                },
            },
            dict(cfg['entryPoints']))                    
        

        self._call_cid(['deploy', 'set', 'entrypoint', 'app2', 'exe', 'file2.exe', 'myTune', '--deployDir', 'setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals({
                'app': {
                    'tool' : 'exe',
                    'path' : 'file.exe',
                    'tune' : {},
                },
                'app2': {
                    'tool' : 'exe',
                    'path' : 'file2.exe',
                    'tune' : {},
                },
            },
            dict(cfg['entryPoints']))
                
        self._call_cid(['deploy', 'set', 'entrypoint', 'app2', 'exe', 'file2.exe', '{"a":true}', '--deployDir', 'setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals({
                'app': {
                    'tool' : 'exe',
                    'path' : 'file.exe',
                    'tune' : {},
                },
                'app2': {
                    'tool' : 'exe',
                    'path' : 'file2.exe',
                    'tune' : {
                        "a" : True,
                    },
                },
            },
            dict(cfg['entryPoints']))
                
    def test_12_set_webmount(self):
        cfg_file = os.path.join('setupdir', 'futoin.json')
        
        self._call_cid(['deploy', 'set', 'webmount', '/', '{"static":true}', '--deployDir', 'setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals({'static': True}, cfg['webcfg']['mounts']['/'])

        self._call_cid(['deploy', 'set', 'webmount', '/gzip', '{"static":true,"gzip":false}', '--deployDir', 'setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals({'static': True, "gzip": False}, cfg['webcfg']['mounts']['/gzip'])

    def test_13_set_tools(self):
        cfg_file = os.path.join('setupdir', 'futoin.json')
        
        self._call_cid(['deploy', 'set', 'tools', 'composer=123', 'php', '--deployDir', 'setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals({'composer': '123', 'php': '*'}, cfg['tools'])

        self._call_cid(['deploy', 'set', 'tools', 'ruby=', '--deployDir', 'setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals({'ruby': '*'}, cfg['tools'])
                
    def test_14_set_toolstune(self):
        cfg_file = os.path.join('setupdir', 'futoin.json')
        
        self._call_cid(['deploy', 'set', 'tooltune', 'exe', '{}', '--deployDir', 'setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals({
                'exe': {},
            },
            dict(cfg['toolTune']))

        self._call_cid(['deploy', 'set', 'tooltune', 'php', 'myTune=123', '--deployDir', 'setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals({
                'exe': {},
                'php': {
                    'myTune' : '123',
                },
            },
            dict(cfg['toolTune']))
        
        self._call_cid(['deploy', 'set', 'tooltune', 'php', 'myTune2=some', '--deployDir', 'setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals({
                'exe': {},
                'php': {
                    'myTune' : '123',
                    'myTune2' : 'some',
                },
            },
            dict(cfg['toolTune']))
                
        self._call_cid(['deploy', 'set', 'tooltune', 'phpfpm', '{"a":true}', '--deployDir', 'setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals({
                'exe': {},
                'php': {
                    'myTune' : '123',
                    'myTune2' : 'some',
                },
                'phpfpm': {
                    'a': True,
                },
            },
            dict(cfg['toolTune']))
                
    def test_20_memdetect_system(self):
        if self.IS_MACOS:
            sysmem = int(_executil.callExternal(['sysctl', '-n', 'hw.memsize'], verbose=False).strip())
        else:
            sysmem = int(self._readFile('/proc/meminfo').split()[1])*1024
            
        ra = ResourceAlgo()
        
        self.assertEqual(sysmem, ra.systemMemory())
        self.assertEqual(sysmem / 2, ra.memoryLimit({}))
    
    def test_20_memdetect_cgroup(self):
        ra = ResourceAlgo()
        
        if os.path.exists('/sys/fs/cgroup/memory/memory.limit_in_bytes'):
            limit_in_bytes = self._readFile('/sys/fs/cgroup/memory/memory.limit_in_bytes')
            limit_in_bytes = int(limit_in_bytes.strip())
            self.assertEqual(limit_in_bytes, ra.cgroupMemory())
        else:
            self.assertEqual(None, ra.cgroupMemory())
        
        self._writeFile('cgroup_mem', '1234567')
        self.assertEqual(1234567, ra.cgroupMemory('cgroup_mem'))
    
    def test_20_memdetect_config(self):
        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--limit-memory=1234M'])
        config = self._readJSON(os.path.join('setupdir', 'futoin.json'))
        self.assertEqual(1234*1024*1024, ResourceAlgo().memoryLimit(config))
        
    def test_30_cpudetect_system(self):
        if self.IS_MACOS:
            cpus = int(_executil.callExternal(['sysctl', '-n', 'hw.ncpu'], verbose=False).strip())
        else:
            cpus = self._readFile('/proc/cpuinfo').split("\n")
            cpus = filter(lambda x: x.split(':')[0].strip() == 'processor', cpus)
            cpus = len(list(cpus))
        
        self.assertEqual(cpus, ResourceAlgo().systemCpuCount())

    def test_30_cpudetect_cgroup(self):
        ra = ResourceAlgo()
        
        self._writeFile('cgroup_cpu', '3')
        self.assertEqual(1, ra.cgroupCpuCount('cgroup_cpu'))
        
        self._writeFile('cgroup_cpu', '3-6')
        self.assertEqual(4, ra.cgroupCpuCount('cgroup_cpu'))
        
        self._writeFile('cgroup_cpu', '1,3-6')
        self.assertEqual(5, ra.cgroupCpuCount('cgroup_cpu'))
        
        self._writeFile('cgroup_cpu', '1,3-6,8\n')
        self.assertEqual(6, ra.cgroupCpuCount('cgroup_cpu'))
        
    def test_30_cpudetect_config(self):
        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--limit-cpus=132'])
        config = self._readJSON(os.path.join('setupdir', 'futoin.json'))
        self.assertEqual(132, ResourceAlgo().cpuLimit(config))
        
    def test_30_distribute(self):
        ra = ResourceAlgo()
        
        config = {
            'deployDir' : 'deploydst',
            'entryPoints': {
                'scalableMono' : {
                    'tool': 'invalid',
                    'tune': {
                        'minMemory' : '100M',
                        'connMemory' : '32K',
                        'memWeight' : 50,
                        'multiCore' : False,
                        'socketTypes' : ['unix'],
                        'maxRequestSize' : '1M',
                        'socketProtocol': 'http',
                    },
                },
                'scalableMulti': {
                    'tool': 'invalid',
                    'tune': {
                        'minMemory' : '3G',
                        'connMemory' : '32M',
                        'memWeight' : 300,
                        'multiCore' : True,
                        'socketTypes' : ['unix', 'tcp'],
                        'socketType' : 'tcp',
                        'socketPort' : 8080,
                        'maxRequestSize' : '1M',
                        'socketProtocol': 'http',
                    },
                },
                'nonScalable' : {
                    'tool': 'invalid',
                    'tune': {
                        'minMemory' : '256M',
                        'maxTotalMemory': '4G',
                        'connMemory' : '16K',
                        'scalable' : False,
                        'socketTypes' : ['unix', 'tcp', 'tcp6'],
                        'socketType' : 'tcp',
                        'maxRequestSize' : '1M',
                        'socketProtocol': 'http',
                    },
                },
            },
            'deploy' : {
                'maxTotalMemory' : '63G',
                'maxCpuCount' : 15,
                'listenAddress' : '127.1.2.3',
            },
        }
            
        ra.configServices(config)
        self._writeJSON('autoservices.json', config)
        
        total_mem = 0
        service_mem = {}
        autoServices = config['deploy']['autoServices']
        
        for (sn, sl) in autoServices.items():
            service_mem[sn] = 0
            for s in sl:
                mem = _configutil.parseMemory(s['maxMemory'])
                _configutil.parseMemory(s['connMemory'])
                total_mem += mem
                service_mem[sn] += mem
                
                if sn == 'scalableMono':
                    self.assertEqual('unix', s['socketType'])
                else:
                    self.assertEqual('tcp', s['socketType'])
                    self.assertEqual('127.1.2.3', s['socketAddress'])
            
        self.assertGreaterEqual(63*1024*1024*1024, total_mem)
        self.assertLessEqual(63*1024*1024*1024 - ra.pageSize(), total_mem)
        
        self.assertEqual(15, len(autoServices['scalableMono']))
        self.assertEqual(2, len(autoServices['scalableMulti']))
        self.assertEqual(1, len(autoServices['nonScalable']))
        
        base = (63-3-4)*1024
        base -= 100
        mb = 1024*1024
        
        self.assertAlmostEqual(int(base * 50 / 350 + 100) * mb, service_mem['scalableMono'], delta=mb)
        self.assertAlmostEqual(int(base * 300 / 350 + 3*1024) * mb, service_mem['scalableMulti'], delta=mb)
        self.assertEqual(4 * 1024 * mb, service_mem['nonScalable'])

class cid_devserve_Test( cid_UTBase ) :
    __test__ = True
    
    TEST_DIR = os.path.join(cid_UTBase.TEST_RUN_DIR, 'devserve')
    _create_test_dir = True
        
    def test_04_devserve(self):
        os.mkdir('devserve')
        os.chdir('devserve')
        
        self._writeFile('longrun.sh', "#!/bin/bash\necho -n 1 >>longrun.txt;sleep 60\n")
        os.chmod('longrun.sh', stat.S_IRWXU)
        self._writeFile('shortrun.sh', "#!/bin/bash\necho -n 1 >>shortrun.txt;sleep 1\n")
        os.chmod('shortrun.sh', stat.S_IRWXU)
        
        self._writeJSON('futoin.json', {
            'entryPoints' : {
                'longrun' : {
                    'tool' : 'exe',
                    'path' : 'longrun.sh'
                },
                'shortrun' : {
                    'tool' : 'exe',
                    'path' : 'shortrun.sh'
                },
                'failing' : {
                    'tool' : 'exe',
                    'path' : 'missing.sh'
                },
            },
        })
                
        pid = os.fork()
        
        if not pid:
            self._redirectAsyncStdIO()
            os.execv(self.CIDTEST_BIN, [self.CIDTEST_BIN, 'devserve'])
            
        time.sleep(15)
        os.kill(pid, signal.SIGTERM)
        try: os.waitpid(pid, 0)
        except OSError: pass
    
        self.assertEqual('1', self._readFile('longrun.txt'))
        # 1,2,delay,3,delay
        self.assertEqual('111', self._readFile('shortrun.txt'))
        
class cid_service_Test( cid_UTBase ) :
    #__test__ = True
    
    TEST_DIR = os.path.join(cid_UTBase.TEST_RUN_DIR, 'service')
    _create_test_dir = True


class cid_multiapp_Base( cid_UTBase ) :
    _create_test_dir = True
    
    def _writeFiles(self):
        pass
    
    def _testApps(self):
        pass
        
    def test_05_multiapp(self):
        os.mkdir('webroot')
        
        self._writeFiles()
        
        self._call_cid(['prepare'])
        self._call_cid(['build'])

        pid = os.fork()
        
        if not pid:
            self._redirectAsyncStdIO()
            os.execv(self.CIDTEST_BIN, [self.CIDTEST_BIN, 'devserve'])
        
        try:
            self._testApps()
        
        finally:
            os.kill(pid, signal.SIGTERM)
            try: os.waitpid(pid, 0)
            except OSError: pass

@attr(tool='php')
class cid_multiphp_Test( cid_multiapp_Base ) :
    __test__ = True
    TEST_DIR = os.path.join(cid_UTBase.TEST_RUN_DIR, 'deploy_php')
    
    def _writeFiles(self):
        self._writeJSON('futoin.json', {
            'entryPoints' : {
                'phpapp' : {
                    'tool' : 'phpfpm',
                    'path' : 'app.php',
                    'tune' : {
                        'internal': True,
                        'memoryWeight' : 70,
                    },
                },
                'phpadminapp' : {
                    'tool' : 'phpfpm',
                    'path' : 'admin.php',
                    'tune' : {
                        'internal': True,
                        'socketType' : 'tcp',
                        'memoryWeight' : 5,
                    },
                },
                'web' : {
                    'tool' : 'nginx',
                    "path" : "webroot",
                    'tune' : {
                        'maxMemory' : '32M',
                        'socketType' : 'tcp',
                        'socketPort' : '1234',
                    },
                },
            },
            'webcfg' : {
                'root' : 'webroot',
                'mounts' : {
                    '/' : {
                        'app' : 'phpapp',
                        'static' : True,
                    },
                    '/admin/' : 'phpadminapp',
                }
            },
        })

        self._writeFile(os.path.join('webroot', 'file.txt'), 'TESTFILE')
        
        self._writeFile('app.php', """<?php
echo "PHP\\n";
""")
        self._writeFile('admin.php', """<?php
echo "ADMINPHP\\n";
""")
        
    def _testApps(self):
        res = self._firstGet('http://127.0.0.1:1234/file.txt')
        self.assertTrue(res.ok)
        self.assertEquals("TESTFILE\n", res.text)
        
        res = self._firstGet('http://127.0.0.1:1234')
        self.assertTrue(res.ok)
        self.assertEquals("PHP\n", res.text)

        res = self._firstGet('http://127.0.0.1:1234/admin/')
        self.assertTrue(res.ok)
        self.assertEquals("ADMINPHP\n", res.text)

@attr(tool='node')
class cid_multijs_Test( cid_multiapp_Base ) :
    __test__ = True
    TEST_DIR = os.path.join(cid_UTBase.TEST_RUN_DIR, 'deploy_js')
        
    def _writeFiles(self):
        os.mkdir('multiapp')
        os.chdir('multiapp')
        
        os.mkdir('webroot')
        
        self._writeJSON('futoin.json', {
            'entryPoints' : {
                'jsapp' : {
                    'tool' : 'node',
                    'path' : 'app.js',
                    'tune' : {
                        'internal': True,
                        'memoryWeight' : 30,
                    },
                },
                'jstcpapp' : {
                    'tool' : 'node',
                    'path' : 'apptcp.js',
                    'tune' : {
                        'internal': True,
                        'socketType' : 'tcp',
                        'memoryWeight' : 5,
                    },
                },
                'web' : {
                    'tool' : 'nginx',
                    "path" : "webroot",
                    'tune' : {
                        'maxMemory' : '32M',
                        'socketType' : 'tcp',
                        'socketPort' : '1234',
                    },
                },
            },
            'webcfg' : {
                'root' : 'webroot',
                'mounts' : {
                    '/' : {
                        'app' : 'jsapp',
                        'static' : True,
                    },
                    '/jstcpapp/' : 'jstcpapp',
                }
            },
        })

        self._writeFile(os.path.join('webroot', 'file.txt'), 'TESTFILE')
        self._writeFile('app.js', """
var http = require('http');

var server = http.createServer(function (request, response) {
  response.writeHead(200, {"Content-Type": "text/plain"});
  response.end("NODEJS\\n");
});

server.listen(process.env.PORT);
""")
        self._writeFile('apptcp.js', """
var http = require('http');

var server = http.createServer(function (request, response) {
  response.writeHead(200, {"Content-Type": "text/plain"});
  response.end("NODEJS-TCP\\n");
});

server.listen(process.env.PORT);
""")

    def _testApps(self):
        res = self._firstGet('http://127.0.0.1:1234/file.txt')     
        self.assertTrue(res.ok)
        self.assertEquals("TESTFILE\n", res.text)
        

        res = self._firstGet('http://127.0.0.1:1234/jsapp/')
        self.assertTrue(res.ok)
        self.assertEquals("NODEJS\n", res.text)

        res = self._firstGet('http://127.0.0.1:1234/jstcpapp/')
        self.assertTrue(res.ok)
        self.assertEquals("NODEJS-TCP\n", res.text)

@attr(tool='python')
class cid_multipy_Test( cid_multiapp_Base ) :
    __test__ = True
    TEST_DIR = os.path.join(cid_UTBase.TEST_RUN_DIR, 'deploy_py')
    
    def _writeFiles(self):
        self._writeJSON('futoin.json', {
            'entryPoints' : {
                'pyapp' : {
                    'tool' : 'uwsgi',
                    'path' : 'app.py',
                    'tune' : {
                        'internal': True,
                        'memoryWeight' : 70,
                    },
                },
                'pytcpapp' : {
                    'tool' : 'uwsgi',
                    'path' : 'apptcp.py',
                    'tune' : {
                        'internal': True,
                        'socketType' : 'tcp',
                        'memoryWeight' : 70,
                    },
                },
                'web' : {
                    'tool' : 'nginx',
                    "path" : "webroot",
                    'tune' : {
                        'maxMemory' : '32M',
                        'socketType' : 'tcp',
                        'socketPort' : '1234',
                    },
                },
            },
            'webcfg' : {
                'root' : 'webroot',
                'mounts' : {
                    '/' : {
                        'app' : 'pyapp',
                        'static' : True,
                    },
                    '/pytcpapp/' : 'pytcpapp',
                }
            },
        })

        self._writeFile(os.path.join('webroot', 'file.txt'), 'TESTFILE')
        
        self._writeFile('app.py', """
def application(env, start_response):
    start_response('200 OK', [('Content-Type','text/html')])
    return [b"PYTHON\\n"]
""")
        
        self._writeFile('apptcp.py', """
def application(env, start_response):
    start_response('200 OK', [('Content-Type','text/html')])
    return [b"PYTHON-TCP\\n"]
""")
        
        
    def _testApps(self):
        res = self._firstGet('http://127.0.0.1:1234/file.txt')
        self.assertTrue(res.ok)
        self.assertEquals("TESTFILE\n", res.text)
        
        res = self._firstGet('http://127.0.0.1:1234')
        self.assertTrue(res.ok)
        self.assertEquals("PYTHON\n", res.text)

        res = self._firstGet('http://127.0.0.1:1234/pytcpapp/')
        self.assertTrue(res.ok)
        self.assertEquals("PYTHON-TCP\n", res.text)
        
@attr(tool='ruby')
class cid_multirb_Test( cid_multiapp_Base ) :
    __test__ = True
    TEST_DIR = os.path.join(cid_UTBase.TEST_RUN_DIR, 'deploy_rb')
    
    def _writeFiles(self):
        self._call_cid(['tool', 'exec', 'bundler', '--', 'init'])
        self._writeJSON('futoin.json', {
            'entryPoints' : {
                'rbapp' : {
                    'tool' : 'puma',
                    'path' : 'app.ru',
                    'tune' : {
                        'internal': True,
                        'minMemory': '8M',
                        'connMemory': '4M',
                    },
                },
                'rbtcpapp' : {
                    'tool' : 'puma',
                    'path' : 'apptcp.ru',
                    'tune' : {
                        'internal': True,
                        'socketType' : 'tcp',
                        'minMemory': '8M',
                        'connMemory': '4M',
                    },
                },
                'web' : {
                    'tool' : 'nginx',
                    "path" : "webroot",
                    'tune' : {
                        'maxMemory' : '32M',
                        'socketType' : 'tcp',
                        'socketPort' : '1234',
                    },
                },
            },
            'webcfg' : {
                'root' : 'webroot',
                'mounts' : {
                    '/' : {
                        'app' : 'rbapp',
                        'static' : True,
                    },
                    '/rbtcpapp/' : 'rbtcpapp',
                }
            },
        })

        self._writeFile(os.path.join('webroot', 'file.txt'), 'TESTFILE')
        
        self._writeFile('app.ru', """
class RubyApp
  def call(env)
    return [
      200,
      {"Content-Type" => "text/plain"},
      ["RUBY\\n"]
    ]
  end
end

run RubyApp.new()                        
""")
        
        self._writeFile('apptcp.ru', """
class RubyApp
  def call(env)
    return [
      200,
      {"Content-Type" => "text/plain"},
      ["RUBY-TCP\\n"]
    ]
  end
end

run RubyApp.new()                        
""")
        
        
    def _testApps(self):
        res = self._firstGet('http://127.0.0.1:1234/file.txt')
        self.assertTrue(res.ok)
        self.assertEquals("TESTFILE\n", res.text)
        
        res = self._firstGet('http://127.0.0.1:1234')
        self.assertTrue(res.ok)
        self.assertEquals("RUBY\n", res.text)

        res = self._firstGet('http://127.0.0.1:1234/rbtcpapp/')
        self.assertTrue(res.ok)
        self.assertEquals("RUBY-TCP\n", res.text)

