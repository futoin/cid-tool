#
# Copyright 2015-2018 Andrey Galkin <andrey@futoin.org>
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

from __future__ import print_function, absolute_import
from nose.plugins.attrib import attr

from .cid_utbase import cid_UTBase
from futoin.cid.rmstool import RmsTool

import os, stat, fcntl
import subprocess
import glob

class cid_runcmd_Test ( cid_UTBase ) :
    __test__ = True
    TEST_DIR = os.path.join(cid_UTBase.TEST_RUN_DIR, 'runcmd')
    
    @classmethod
    def setUpClass( cls ):
        super(cid_runcmd_Test, cls).setUpClass()
        
        os.mkdir(cls.TEST_DIR)
        os.chdir(cls.TEST_DIR)
        
        cls._writeFile('exe_file.sh', "#!/bin/sh\necho EXE" )
        os.chmod('exe_file.sh', stat.S_IRWXU )
        cls._writeFile('go_file.go', """
package main
import "fmt"

func main() {
    fmt.Println("GO")
}
""")
        
        cls._writeFile('build.gradle', """
apply plugin: 'java'

jar {
    archiveName = 'java_file.jar'
    manifest {
        attributes 'Main-Class': 'org.futoin.javatest.Hello'
    }
}
""")
        javatest_dir = os.path.join('src', 'main', 'java', 'org', 'futoin', 'javatest')
        os.makedirs(javatest_dir)
        cls._writeFile(os.path.join(javatest_dir, 'Hello.java'), """
package org.futoin.javatest;
 
public class Hello {
 
    public static void main(String[] args) {
        System.out.println("JAVA");
    }
}
""")
        
        cls._writeFile('node_file.js', """
console.log('NODE');
""")
        
        cls._writeFile('php_file.php', """<?php
echo "PHP\n";
""")
        
        cls._writeFile('python_file.py', """
print('PYTHON');
""")
        
        cls._writeFile('ruby_file.rb', """
puts 'RUBY'
""")
        
        cls._writeFile('scala_file.scala', '''
object Hi {
  def main(args: Array[String]) = println("SCALA")
}
''')

        cls._writeJSON('futoin.json', {
            "name": "cid-runcmd-test",
            "version": "0.0.1",
            "actions": {
                "custom_str": "echo CustomCommand",
                "custom_list": [
                    "echo CustomList1",
                    "echo CustomList2",
                ],
                "test-cid" : "@cid tool exec bash -- -c 'echo FROM-SUB-CID'",
            },
            "entryPoints": {
                'exe_ep' : {
                    'tool': 'exe',
                    'path': 'exe_file.sh',
                },
                'go_ep' : {
                    'tool': 'go',
                    'path': 'go_file.go',
                },
                'java_ep' : {
                    'tool': 'java',
                    'path': 'build/libs/java_file.jar',
                },
                'node_ep' : {
                    'tool': 'node',
                    'path': 'node_file.js',
                },
                'php_ep' : {
                    'tool': 'php',
                    'path': 'php_file.php',
                },
                'python_ep' : {
                    'tool': 'python',
                    'path': 'python_file.py',
                },
                'ruby_ep' : {
                    'tool': 'ruby',
                    'path': 'ruby_file.rb',
                },
                'scala_ep' : {
                    'tool': 'scala',
                    'path': 'scala_file.scala',
                },
            },
            "toolTune" : {
                "gradle": {
                    "package": "jar",
                }
            },
        })
                
        cls._call_cid(['tool', 'package', 'gradle'])
            
    def _test_run(self, cmd, expect):
        res = self._call_cid(['run', cmd], retout=True).strip()
        self.assertEqual(res, expect)
            
    def test10_run_custom_str( self ):
        self._test_run('custom_str', 'CustomCommand')
        
    def test11_run_custom_list( self ):
        self._test_run('custom_list', 'CustomList1\nCustomList2')

    def test12_run_test_cid(self):
        self._test_run('test-cid', 'FROM-SUB-CID')
    
    def test20_run_exe_ep( self ):
        self._test_run('exe_ep', 'EXE')
    
    @attr(tool='go')
    def test21_run_go_ep( self ):
        self._test_run('go_ep', 'GO')
    
    @attr(tool='java')
    def test22_run_java_ep( self ):
        self._test_run('java_ep', 'JAVA')
    
    @attr(tool='node')
    def test23_run_node_ep( self ):
        self._test_run('node_ep', 'NODE')
    
    @attr(tool='php')
    def test24_run_php_ep( self ):
        self._test_run('php_ep', 'PHP')
    
    @attr(tool='python')
    def test24_run_python_ep( self ):
        self._test_run('python_ep', 'PYTHON')
    
    @attr(tool='ruby')
    def test25_run_ruby_ep( self ):
        self._test_run('ruby_ep', 'RUBY')
    
    @attr(tool='java')
    def test26_run_scala_ep( self ):
        self._test_run('scala_ep', 'SCALA')
    
    def test50_run_all( self ):
        res= self._call_cid(['run'], retout=True)
        res = sorted(res.strip().split("\n"))

        expect = sorted([
            'EXE',
            'GO',
            'JAVA',
            'NODE',
            'PHP',
            'PYTHON',
            'RUBY',
            'SCALA'
        ])
        
        self.assertEqual(res, expect)
        
    
