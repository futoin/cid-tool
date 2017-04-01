
from __future__ import print_function, absolute_import

from .citool_utbase import citool_UTBase
from futoin.cid.rmstool import RmsTool

import os, stat
import subprocess
import glob

class cid_runcmd_Test ( citool_UTBase ) :
    __test__ = True
    TEST_DIR = os.path.join(citool_UTBase.TEST_RUN_DIR, 'runcmd')
    
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
        
        cls._writeFile('php_file.php', """
<?php
echo 'PHP';
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
            },
            "entryPoints": {
                'exe_ep' : {
                    'tool': 'exe',
                    'file': 'exe_file.sh',
                },
                'go_ep' : {
                    'tool': 'go',
                    'file': 'go_file.go',
                },
                'java_ep' : {
                    'tool': 'java',
                    'file': 'build/libs/java_file.jar',
                },
                'node_ep' : {
                    'tool': 'node',
                    'file': 'node_file.js',
                },
                'php_ep' : {
                    'tool': 'php',
                    'file': 'php_file.php',
                },
                'python_ep' : {
                    'tool': 'python',
                    'file': 'python_file.py',
                },
                'ruby_ep' : {
                    'tool': 'ruby',
                    'file': 'ruby_file.rb',
                },
                'scala_ep' : {
                    'tool': 'scala',
                    'file': 'scala_file.scala',
                },
            },
            "toolTune" : {
                "gradle": {
                    "package": "jar",
                }
            }
        })
                
        cls._call_citool(['tool', 'package', 'gradle'])
            
    def _test_run(self, cmd, expect):
        (r, w) = os.pipe()
        self._call_citool(['run', cmd], stdout=w)
        res = os.read(r, 1024).strip()
        os.close(r)
        os.close(w)
        
        try:
            res = str(res, 'utf8')
        except:
            pass
        
        self.assertEqual(res, expect)
            
    def test10_run_custom_str( self ):
        self._test_run('custom_str', 'CustomCommand')
        
    def test11_run_custom_list( self ):
        self._test_run('custom_list', 'CustomList1\nCustomList2')

    def test20_run_exe_ep( self ):
        self._test_run('exe_ep', 'EXE')
        
    def test21_run_go_ep( self ):
        self._test_run('go_ep', 'GO')
        
    def test22_run_java_ep( self ):
        self._test_run('java_ep', 'JAVA')
    
    def test23_run_node_ep( self ):
        self._test_run('node_ep', 'NODE')
    
    def test24_run_php_ep( self ):
        self._test_run('php_ep', 'PHP')
    
    def test24_run_python_ep( self ):
        self._test_run('python_ep', 'PYTHON')
    
    def test25_run_ruby_ep( self ):
        self._test_run('ruby_ep', 'RUBY')
    
    def test26_run_scala_ep( self ):
        self._test_run('scala_ep', 'SCALA')
    