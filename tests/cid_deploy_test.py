
import os
import sys
import time
import signal
import stat

from .cid_utbase import cid_UTBase
from futoin.cid.details.resourcealgo import ResourceAlgo
from futoin.cid.mixins.util import UtilMixIn

class cid_deploy_Test( cid_UTBase, UtilMixIn ) :
    __test__ = True
    
    TEST_DIR = os.path.join(cid_UTBase.TEST_RUN_DIR, 'deploycmd')
    _create_test_dir = True
        
    def test_01_setup(self):
        cfg_file = os.path.join('setupdir', 'futoin.json')
        
        runtime_dir = os.path.join(self.TEST_DIR, 'setupdir', '.runtime')
        
        self._call_cid(['deploy', 'setup', '--deployDir=setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(dict(cfg['deploy']), {
            'runtimeDir' : runtime_dir,
            'autoServices': {},
            'user' : 'vagrant',
            'group' : 'vagrant',
        })
        
        self._call_cid(['deploy', 'setup', '--deployDir=setupdir', '--runtimeDir=/tmp/someother'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(dict(cfg['deploy']), {
            'autoServices': {},
            'runtimeDir' : '/tmp/someother',
            'user' : 'vagrant',
            'group' : 'vagrant',
        })

        self._call_cid(['deploy', 'setup', '--deployDir=setupdir'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(dict(cfg['deploy']), {
            'autoServices': {},
            'runtimeDir' : '/tmp/someother',
            'user' : 'vagrant',
            'group' : 'vagrant',
        })

        self._call_cid(['deploy', 'setup', '--deployDir=setupdir', '--runtimeDir=auto'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(dict(cfg['deploy']), {
            'runtimeDir' : runtime_dir,
            'autoServices': {},
            'user' : 'vagrant',
            'group' : 'vagrant',
        })
        
        
        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--listen-addr=1.2.3.4'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(dict(cfg['deploy']), {
            'runtimeDir' : runtime_dir,
            'autoServices': {},
            'listenAddress': '1.2.3.4',
            'user' : 'vagrant',
            'group' : 'vagrant',
        })
        
        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--limit-cpus=3'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(dict(cfg['deploy']), {
            'runtimeDir' : runtime_dir,
            'autoServices': {},
            'maxCpuCount': 3,
            'listenAddress': '1.2.3.4',
            'user' : 'vagrant',
            'group' : 'vagrant',
        })
        
        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--limit-memory=18M'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(dict(cfg['deploy']), {
            'runtimeDir' : runtime_dir,
            'autoServices': {},
            'maxTotalMemory' : '18M',
            'maxCpuCount': 3,
            'listenAddress': '1.2.3.4',
            'user' : 'vagrant',
            'group' : 'vagrant',
        })

        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--limit-memory=auto'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(dict(cfg['deploy']), {
            'runtimeDir' : runtime_dir,
            'autoServices': {},
            'maxCpuCount': 3,
            'listenAddress': '1.2.3.4',
            'user' : 'vagrant',
            'group' : 'vagrant',
        })

        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--limit-cpus=auto'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(dict(cfg['deploy']), {
            'runtimeDir' : runtime_dir,
            'autoServices': {},
            'listenAddress': '1.2.3.4',
            'user' : 'vagrant',
            'group' : 'vagrant',
        })
        
        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--user=someuser',
                        '--group=somegroup'])
        cfg = self._readJSON(cfg_file)
        self.assertEquals(dict(cfg['deploy']), {
            'runtimeDir' : runtime_dir,
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
            'autoServices': {},
            'listenAddress': '1.2.3.4',
            'user' : 'vagrant',
            'group' : 'vagrant',
        })
                
    def test_02_memdetect_system(self):
        sysmem = int(self._readFile('/proc/meminfo').split()[1])*1024
        ra = ResourceAlgo()
        
        self.assertEqual(sysmem, ra.systemMemory())
        self.assertEqual(sysmem / 2, ra.memoryLimit({}))
    
    def test_02_memdetect_cgroup(self):
        ra = ResourceAlgo()
        
        if os.path.exists('/sys/fs/cgroup/memory/memory.limit_in_bytes'):
            self.assertEqual(sys.maxint, ra.cgroupMemory())
        else:
            self.assertEqual(None, ra.cgroupMemory())
        
        self._writeFile('cgroup_mem', '1234567')
        self.assertEqual(1234567, ra.cgroupMemory('cgroup_mem'))
    
    def test_02_memdetect_config(self):
        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--limit-memory=1234M'])
        config = self._readJSON(os.path.join('setupdir', 'futoin.json'))
        self.assertEqual(1234*1024*1024, ResourceAlgo().memoryLimit(config))
        
    def test_03_cpudetect_system(self):
        cpus = self._readFile('/proc/cpuinfo').split("\n")
        cpus = filter(lambda x: x.split(':')[0].strip() == 'processor', cpus)
        cpus = len(list(cpus))
        
        self.assertEqual(cpus, ResourceAlgo().systemCpuCount())

    def test_03_cpudetect_cgroup(self):
        ra = ResourceAlgo()
        
        self._writeFile('cgroup_cpu', '3')
        self.assertEqual(1, ra.cgroupCpuCount('cgroup_cpu'))
        
        self._writeFile('cgroup_cpu', '3-6')
        self.assertEqual(4, ra.cgroupCpuCount('cgroup_cpu'))
        
        self._writeFile('cgroup_cpu', '1,3-6')
        self.assertEqual(5, ra.cgroupCpuCount('cgroup_cpu'))
        
        self._writeFile('cgroup_cpu', '1,3-6,8\n')
        self.assertEqual(6, ra.cgroupCpuCount('cgroup_cpu'))
        
    def test_03_cpudetect_config(self):
        self._call_cid(['deploy', 'setup',
                        '--deployDir', 'setupdir',
                        '--limit-cpus=132'])
        config = self._readJSON(os.path.join('setupdir', 'futoin.json'))
        self.assertEqual(132, ResourceAlgo().cpuLimit(config))
        
    def test_03_distribute(self):
        ra = ResourceAlgo()
        
        config = {
            'deployDir' : 'deploydst',
            'entryPoints': {
                'scalableMono' : {
                    'tune': {
                        'minMemory' : '100M',
                        'connMemory' : '32K',
                        'memWeight' : 50,
                        'multiCore' : False,
                        'socketTypes' : ['unix'],
                    },
                },
                'scalableMulti': {
                    'tune': {
                        'minMemory' : '3G',
                        'connMemory' : '32M',
                        'memWeight' : 300,
                        'multiCore' : True,
                        'socketTypes' : ['unix', 'tcp'],
                        'socketType' : 'tcp',
                        'socketPort' : 8080,
                    },
                },
                'nonScalable' : {
                    'tune': {
                        'minMemory' : '256M',
                        'maxTotalMemory': '4G',
                        'connMemory' : '16K',
                        'scalable' : False,
                        'socketTypes' : ['unix', 'tcp', 'tcp6'],
                        'socketType' : 'tcp',
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
                mem = self._parseMemory(s['maxMemory'])
                self._parseMemory(s['connMemory'])
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

class cid_devserve_Test( cid_UTBase, UtilMixIn ) :
    __test__ = True
    
    TEST_DIR = os.path.join(cid_UTBase.TEST_RUN_DIR, 'deploycmd')
    _create_test_dir = True
        
    def test_04_devserve(self):
        os.mkdir('devserve')
        os.chdir('devserve')
        
        self._writeFile('longrun.sh', "#!/bin/sh\necho -n 1 >>longrun.txt;sleep 60\n")
        os.chmod('longrun.sh', stat.S_IRWXU)
        self._writeFile('shortrun.sh', "#!/bin/sh\necho -n 1 >>shortrun.txt;sleep 1\n")
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
            os.dup2(os.open(os.devnull, os.O_RDONLY), 0)
            os.dup2(os.open(os.devnull, os.O_WRONLY), 1)
            os.dup2(os.open(os.devnull, os.O_WRONLY), 2)
            os.execv(self.CIDTEST_BIN, [self.CIDTEST_BIN, 'devserve'])
            
        time.sleep(15)
        os.kill(pid, signal.SIGTERM)
        try: os.waitpid(pid, 0)
        except OSError: pass
    
        self.assertEqual(1, len(self._readFile('longrun.txt')))
        # 1,2,delay,3,delay
        self.assertEqual(3, len(self._readFile('shortrun.txt')))

        
class cid_multiapp_Test( cid_UTBase, UtilMixIn ) :
    __test__ = True
    
    TEST_DIR = os.path.join(cid_UTBase.TEST_RUN_DIR, 'deploycmd')
    _create_test_dir = True
        
    def test_05_multiapp(self):
        os.mkdir('multiapp')
        os.chdir('multiapp')
        
        os.mkdir('webroot')
        
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
                        'memoryWeight' : 5,
                    },
                },
                #'jsapp' : {
                    #'tool' : 'node',
                    #'path' : 'app.js',
                    #'tune' : {
                        #'socketType' : 'tcp',
                        #'memoryWeight' : 30,
                    #},
                #},
                #'rubyapp' : {
                    #'tool' : 'rack',
                #},
                #'pythonapp' : {
                    #'tool' : 'uwsgi',
                #},
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
                'main' : 'phpapp',
                'mounts' : {
                    '/admin/' : 'phpadminapp',
                    #'/jsapp/' : 'jsapp',
                    #'/rubyapp/' : 'rubyapp',
                    #'/pythonapp/' : 'pythonapp',
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
        self._writeFile('app.js', """
var http = require('http');

var server = http.createServer(function (request, response) {
  response.writeHead(200, {"Content-Type": "text/plain"});
  response.end("Node.js\\n");
});

server.listen(process.env.PORT || process.env.HTTP_PORT);
""")
        self._writeFile('config.ru', """
class RubyApp
  def call(env)
    return [
      200,
      {"Content-Type" => "text/plain"},
      ["Ruby\\n"]
    ]
  end
end

run RubyApp.new()                        
""")
        
        self._writeFile('app.py', """
def application(env, start_response):
    start_response('200 OK', [('Content-Type','text/html')])
    return [b"Python\n"]
""")
        pid = os.fork()
        
        if not pid:
            os.dup2(os.open(os.devnull, os.O_RDONLY), 0)
            #os.dup2(os.open(os.devnull, os.O_WRONLY), 1)
            #os.dup2(os.open(os.devnull, os.O_WRONLY), 2)
            os.execv(self.CIDTEST_BIN, [self.CIDTEST_BIN, 'devserve'])
            
        time.sleep(300)
        
        try:
            import requests
            res = requests.get('http://localhost:1234/file.txt')
            self.assertTrue(res.ok)
            self.assertEquals("TESTFILE", res.text)
            
            res = requests.get('http://localhost:1234')
            self.assertTrue(res.ok)
            self.assertEquals("PHP\n", res.text)

            res = requests.get('http://localhost:1234/admin')
            self.assertTrue(res.ok)
            self.assertEquals("ADMINPHP\n", res.text)
        
        finally:
            os.kill(pid, signal.SIGTERM)
            try: os.waitpid(pid, 0)
            except OSError: pass
