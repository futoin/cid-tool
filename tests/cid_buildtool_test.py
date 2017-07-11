
from .cid_utbase import cid_Tool_UTBase
import os, re, sys, subprocess, platform, glob, stat
from futoin.cid.util import pathutil
from nose.plugins.attrib import attr

#=============================================================================
class cid_BuildTool_UTBase(cid_Tool_UTBase):
    @classmethod
    def setUpClass(cls):
        cls.TOOL_NAME = re.match(r'^cid_(.+)_Test$', cls.__name__).group(1)
        super(cid_BuildTool_UTBase, cls).setUpClass()
        cls.setUpTool()

    @classmethod
    def setUpTool(cls):
        pass
    
    def test10_prepare( self ):
        self._call_cid( [ 'prepare' ] )
        self._test_prepare()
        
    def test20_build( self ):
        self._call_cid( [ 'build' ] )
        self._test_build()

    def test30_package( self ):
        self._call_cid( [ 'package' ] )
        self._test_package()
        
    def test40_tool_detect( self ):
        res = self._call_cid( [ 'tool', 'detect' ], retout=True )
        
        for l in res.split("\n"):
            if l.split('=')[0] == self.TOOL_NAME:
                break
        else:
            raise RuntimeError('Failed to find the tool in detection')
        
    def _test_prepare( self ):
        pass
    
    def _test_build( self ):
        pass
    
    def _test_package( self ):
        pass


#=============================================================================
@attr(tool='java')
class cid_ant_Test(cid_BuildTool_UTBase):
    __test__ = True
    
    @classmethod
    def setUpTool(cls):
        os.makedirs(os.path.join('src', 'oata'))
        cls._writeFile(os.path.join('src', 'oata', 'HelloWorld.java'), '''
package oata;

public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}                       
''')
        
        cls._writeFile('build.xml', '''
<project>

    <target name="clean">
        <delete dir="build"/>
    </target>

    <target name="compile">
        <mkdir dir="build/classes"/>
        <javac srcdir="src" destdir="build/classes"/>
    </target>

    <target name="jar">
        <mkdir dir="build/jar"/>
        <jar destfile="build/jar/HelloWorld.jar" basedir="build/classes">
            <manifest>
                <attribute name="Main-Class" value="oata.HelloWorld"/>
            </manifest>
        </jar>
    </target>

    <target name="run">
        <java jar="build/jar/HelloWorld.jar" fork="true"/>
    </target>

</project>
''')
        
    def _test_build( self ):
        assert os.path.exists('build/classes/oata/HelloWorld.class')
        assert not os.path.exists('build/jar/HelloWorld.jar')

    def _test_package( self ):
        assert os.path.exists('build/jar/HelloWorld.jar')


#=============================================================================
@attr(tool='node')
class cid_bower_Test(cid_BuildTool_UTBase):
    __test__ = True
    
    @classmethod
    def setUpTool(cls):
        cls._writeJSON('bower.json', {
            "name": "cid-bower-test",
            "description": "Futoin CID Bower Test",
            "dependencies": {
                "get-size": "~1.2.2"
            },
            "devDependencies": {
                "qunit": "~1.16.0"
            },
        })
        
    def _test_prepare( self ):
        assert os.path.exists('bower_components/get-size')
        assert os.path.exists('bower_components/qunit')

    def _test_package( self ):
        assert os.path.exists('bower_components/get-size')
        assert not os.path.exists('bower_components/qunit')


#=============================================================================
@attr(tool='ruby')
class cid_bundler_Test(cid_BuildTool_UTBase):
    __test__ = True
    
    @classmethod
    def setUpTool(cls):
        cls._writeFile('Gemfile', '''
source 'https://rubygems.org'
gem 'thor', '0.19.1'
''')
        
    def _test_prepare( self ):
        with open('res.txt', 'w') as f:
            self._call_cid( [ 'tool', 'exec', 'gem', '--', 'list' ], stdout=f )
            
        with open('res.txt', 'r') as f:
            res = f.readlines()
            
            try:
                res.index('thor (0.19.1)\n')
            except:
                try:
                    res.index('thor (0.19.1)')
                except:
                    self._stderr_log.write(str(res))
                    raise


#=============================================================================
@attr(tool='rust')
class cid_cargo_Test(cid_BuildTool_UTBase):
    __test__ = True
    
    @classmethod
    def setUpTool(cls):
        cls._call_cid( [
            'tool', 'exec', cls.TOOL_NAME, '--',
            'init', '--bin', '--name', 'hello',
        ] )
        
    def _test_build( self ):
        assert os.path.exists('target/release')
        assert not os.path.exists('target/debug')
        
    def _test_package( self ):
        assert glob.glob('target/package/*.crate')

#=============================================================================
class cid_cmake_Test(cid_BuildTool_UTBase):
    __test__ = True
    
    @classmethod
    def setUpTool(cls):
        cls._writeFile('hello.cpp', '''
int main(int, const char**){
    return 0;
}
''')
        cls._writeFile('CMakeLists.txt', '''
cmake_minimum_required (VERSION 2.8.11)
project (HELLO)
add_executable (helloDemo hello.cpp)
''')
        
        
    def _test_build( self ):
        assert os.path.exists('build/Makefile')
        assert os.path.exists('build/helloDemo')


#=============================================================================
php_ver = subprocess.check_output("echo '<?php echo phpversion();' | php 2>/dev/null || echo '5.4'", shell=True)

try:
    php_ver = str(php_ver, 'utf8')
except:
    pass

if php_ver < '5.5':
    composer_require = 'psr/log'
    composer_require_dev = 'symfony/polyfill-mbstring'
else :
    composer_require = "futoin/core-php-ri-asyncsteps"
    composer_require_dev = "futoin/core-php-ri-executor"

@attr(tool='php')
class cid_composer_Test(cid_BuildTool_UTBase):
    __test__ = True
    
    @classmethod
    def setUpTool(cls):
        cls._writeJSON('composer.json', {
            "name": "futoin/cid-composer-test",
            "version" : "0.0.1",
            "description": "Futoin CID Composer Test",
            "require": {
                composer_require: "*"
            },
            "require-dev": {
                composer_require_dev: "*"
            },
        })
        
    def _test_prepare( self ):
        assert os.path.exists('vendor/' + composer_require)
        assert os.path.exists('vendor/' + composer_require_dev)

    def _test_package( self ):
        assert os.path.exists('vendor/' + composer_require)
        assert not os.path.exists('vendor/' + composer_require_dev)

#=============================================================================
class cid_docker_Test(cid_BuildTool_UTBase):
    __test__ = cid_Tool_UTBase.IS_LINUX
    
    @classmethod
    def setUpTool(cls):
        cls._writeFile('Dockerfile', '''
FROM busybox
CMD echo "Hello World!"
''')

#=============================================================================
@attr(tool='java')
class cid_gradle_Test(cid_BuildTool_UTBase):
    __test__ = True
    
    @classmethod
    def setUpTool(cls):
        cls._writeFile('build.gradle', '''
defaultTasks 'test_file'
task clean {}
task dists {}
task test_file {
    doLast {
        File tf = file('test_file.txt')
        tf.text = 'Yes'
    }
}
''')
        cls._writeJSON('futoin.json', {
            'toolTune': {
                'gradle': {
                    'packageGlob' : '*.txt',
                },
            },
        })
        
    def _test_build( self ):
        with open('test_file.txt', 'r') as f:
            res = f.readlines()
            res.index('Yes')


#=============================================================================
@attr(tool='node')
class cid_grunt_Test(cid_BuildTool_UTBase):
    __test__ = True
    
    @classmethod
    def setUpTool(cls):
        cls._writeFile('Gruntfile.js', '''
var fs = require('fs');
module.exports = function(grunt) {
    grunt.initConfig({ pkg: grunt.file.readJSON('package.json') });
    grunt.registerTask('default', function(){
        fs.writeFileSync('test_file.txt', 'Yes');
    });
};
''')
        cls._writeJSON('package.json', {
            "name": "futoin-cid-grunt-test",
            "version" : "0.0.1",
            "description": "Futoin CID grunt Test",
            "devDependencies": {
                "grunt": "*"
            },
        })
        cls._call_cid( [ 'tool', 'prepare', 'npm' ] )
        
        
    def _test_build( self ):
        with open('test_file.txt', 'r') as f:
            res = f.readlines()
            res.index('Yes')


#=============================================================================
@attr(tool='node')
class cid_gulp_Test(cid_BuildTool_UTBase):
    __test__ = True
    
    @classmethod
    def setUpTool(cls):
        cls._writeFile('gulpfile.js', '''
var gulp = require('gulp');
var fs = require('fs');

gulp.task('default', function() {
    fs.writeFileSync('test_file.txt', 'Yes');
});
''')
        cls._writeJSON('package.json', {
            "name": "futoin-cid-gulp-test",
            "version" : "0.0.1",
            "description": "Futoin CID gulp Test",
            "devDependencies": {
                "gulp": "*"
            },
        })
            
        cls._call_cid( [ 'tool', 'prepare', 'npm' ] )
        
        
    def _test_build( self ):
        with open('test_file.txt', 'r') as f:
            res = f.readlines()
            res.index('Yes')


#=============================================================================
class cid_make_Test(cid_BuildTool_UTBase):
    __test__ = True
    
    @classmethod
    def setUpTool(cls):
        cls._writeFile('Makefile', '''
sometarget:
\techo Yes > test_file.txt
clean:
\trm -f test_file.txt
''')
        
    def _test_build( self ):
        with open('test_file.txt', 'r') as f:
            res = f.readlines()
            res.index('Yes\n')


#=============================================================================
@attr(tool='java')
class cid_maven_Test(cid_BuildTool_UTBase):
    __test__ = True
    
    @classmethod
    def setUpTool(cls):
        cls._call_cid( [
            'tool', 'exec', cls.TOOL_NAME, '--',
            'archetype:generate', '-DgroupId=com.mycompany.app',
            '-DartifactId=my-app', '-DarchetypeArtifactId=maven-archetype-quickstart',
            '-DinteractiveMode=false',
        ] )
        
    def setUp( self ):
        cid_BuildTool_UTBase.setUp( self )
        os.chdir( os.path.join(self.TEST_DIR, 'my-app') )
        
    def _test_build( self ):
        assert os.path.exists('target')

    def _test_package( self ):
        assert os.path.exists('target/my-app-1.0-SNAPSHOT.jar')


#=============================================================================
@attr(tool='node')
class cid_npm_Test(cid_BuildTool_UTBase):
    __test__ = True
    
    @classmethod
    def setUpTool(cls):
        cls._writeJSON('package.json', {
            "name": "futoin-cid-npm-test",
            "version" : "0.0.1",
            "description": "Futoin CID npm Test",
            "dependencies": {
                "futoin-asyncsteps": "*"
            },
            "devDependencies": {
                "futoin-executor": "*"
            },
        })
        
    def _test_prepare( self ):
        assert os.path.exists('node_modules/futoin-asyncsteps')
        assert os.path.exists('node_modules/futoin-executor')

    def _test_package( self ):
        assert os.path.exists('node_modules/futoin-asyncsteps')
        assert not os.path.exists('node_modules/futoin-executor')


#=============================================================================
@attr(tool='python')
class cid_pip_Test(cid_BuildTool_UTBase):
    __test__ = True
    
    @classmethod
    def setUpTool(cls):
        cls._writeFile('requirements.txt', '''
nose==1.3.7
''')
        
    def _test_prepare( self ):
        with open('req.txt', 'w') as f:
            self._call_cid( [ 'tool', 'exec', self.TOOL_NAME, '--', 'freeze' ], stdout=f )
            
        with open('req.txt', 'r') as f:
            res = f.readlines()
            res.index('nose==1.3.7\n')


#=============================================================================
class cid_puppet_Test(cid_BuildTool_UTBase):
    __test__ = True
    
    @classmethod
    def setUpTool(cls):
        cls._writeJSON('metadata.json', {
  "name": "futoin-cidpuppettest",
  "version": "0.0.1",
  "summary": "Futoin CID Puppet Test",
})
        os.mkdir('pkg')
        
    def _test_prepare( self ):
        assert not os.path.exists('pkg')
        
    def _test_build( self ):
        assert os.path.exists('pkg')
        
    def _test_package( self ):
        assert os.path.exists('pkg/futoin-cidpuppettest-0.0.1.tar.gz')


#=============================================================================
# SBT takes very long time for initial startup
@attr(tool='java')
class cid_sbt_Test(cid_BuildTool_UTBase):
    __test__ = cid_BuildTool_UTBase.ALLOW_SRC_BUILDS
    
    @classmethod
    def setUpTool(cls):
        cls._writeFile('hello.scala', '''
object Hi {
  def main(args: Array[String]) = println("Hi!")
}
''')
    
        cls._writeFile('build.sbt', '''
name := "hello"

version := "0.1"
''')
        
    def _test_build( self ):
        assert os.path.exists('target')
        assert not glob.glob('target/scala-*/hello_*-0.1.jar')

    def _test_package( self ):
        assert glob.glob('target/scala-*/hello_*-0.1.jar')


#=============================================================================
@attr(tool='python')
class cid_setuptools_Test(cid_BuildTool_UTBase):
    __test__ = True
    
    @classmethod
    def setUpTool(cls):
        os.mkdir('ftntest')
        cls._writeFile('ftntest/__init__.py', '''
def test():
    print "Test"
''')
        cls._writeFile('setup.cfg', '''
[bdist_wheel]
universal=1
''')
        cls._writeFile('setup.py', '''
from setuptools import setup, find_packages

setup(
    name="futoin-cid-testapp",
    version="0.0.1",
    long_description=__doc__,
    packages=find_packages(),
    zip_safe=False,
)
''')
        
    def _test_build( self ):
        assert os.path.exists('dist/futoin_cid_testapp-0.0.1-py2.py3-none-any.whl')
        assert os.path.exists('dist/futoin-cid-testapp-0.0.1.tar.gz')
        
#=============================================================================
@attr(tool='node')
class cid_webpack_Test(cid_BuildTool_UTBase):
    __test__ = True
    
    @classmethod
    def setUpTool(cls):
        cls._writeFile('file.js', """
// Some boring stuff here
console.log('hello');
""")
        cls._writeFile('webpack.config.js', """
const path = require('path');

module.exports = {
  entry: path.resolve(__dirname, 'file.js'),
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'bundle.js'
  }
};
""")
       
        
    def _test_build( self ):
        assert os.path.exists('dist/bundle.js')

#=============================================================================
@attr(tool='node')
class cid_yarn_Test(cid_BuildTool_UTBase):
    __test__ = True
    
    @classmethod
    def setUpTool(cls):
        cls._writeJSON('package.json', {
            "name": "futoin-cid-npm-test",
            "version" : "0.0.1",
            "description": "Futoin CID npm Test",
            "dependencies": {
                "futoin-asyncsteps": "*"
            },
            "devDependencies": {
                "futoin-executor": "*"
            },
        })
        cls._call_cid(['tool', 'exec', 'yarn', '--', 'install'])
        pathutil.rmTree('node_modules', False)
        
        
    def _test_prepare( self ):
        assert os.path.exists('node_modules/futoin-asyncsteps')
        assert os.path.exists('node_modules/futoin-executor')

    def _test_package( self ):
        assert os.path.exists('node_modules/futoin-asyncsteps')
        assert not os.path.exists('node_modules/futoin-executor')
        