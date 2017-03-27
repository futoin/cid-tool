
from .citool_tools_test import citool_Tool_UTBase
import os, re, sys, subprocess

class cid_UTBase(citool_Tool_UTBase):
    __test__ = True
    
    @classmethod
    def setUpClass(cls):
        cls.TOOL_NAME = re.match(r'^cid_(.+)_Test$', cls.__name__).group(1)
        super(cid_UTBase, cls).setUpClass()
        cls.setUpTool()

    @classmethod
    def setUpTool(cls):
        pass


class cid_bower_Test(cid_UTBase):
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
        
    def test10_prepare( self ):
        self._call_citool( [ 'tool', 'prepare', self.TOOL_NAME ] )
        assert os.path.exists('bower_components/get-size')
        assert os.path.exists('bower_components/qunit')

    def test20_package( self ):
        self._call_citool( [ 'tool', 'package', self.TOOL_NAME ] )
        assert os.path.exists('bower_components/get-size')
        assert not os.path.exists('bower_components/qunit')


class cid_bundler_Test(cid_UTBase):
    @classmethod
    def setUpTool(cls):
        cls._writeFile('Gemfile', '''
source 'https://rubygems.org'
gem 'thor', '0.19.1'
''')
        
    def test10_prepare( self ):
        self._call_citool( [ 'tool', 'prepare', self.TOOL_NAME ] )
        
        with open('res.txt', 'w') as f:
            self._call_citool( [ 'tool', 'exec', 'gem', '--', 'list' ], stdout=f )
            
        with open('res.txt', 'r') as f:
            res = f.readlines()
            res.index('thor (0.19.1)\n')

    def test20_package( self ):
        self._call_citool( [ 'tool', 'package', self.TOOL_NAME ] )


class cid_cmake_Test(cid_UTBase):
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
        
    def test10_prepare( self ):
        self._call_citool( [ 'tool', 'prepare', self.TOOL_NAME ] )
        assert os.path.exists('Makefile')


class cid_composer_Test(cid_UTBase):
    @classmethod
    def setUpTool(cls):
        cls._writeJSON('composer.json', {
            "name": "futoin/cid-composer-test",
            "version" : "0.0.1",
            "description": "Futoin CID Composer Test",
            "require": {
                "futoin/core-php-ri-asyncsteps": "*"
            },
            "require-dev": {
                "futoin/core-php-ri-executor": "*"
            },
        })
        
    def test10_prepare( self ):
        self._call_citool( [ 'tool', 'prepare', self.TOOL_NAME ] )
        assert os.path.exists('vendor/futoin/core-php-ri-asyncsteps')
        assert os.path.exists('vendor/futoin/core-php-ri-executor')

    def test20_package( self ):
        self._call_citool( [ 'tool', 'package', self.TOOL_NAME ] )
        assert os.path.exists('vendor/futoin/core-php-ri-asyncsteps')
        assert not os.path.exists('vendor/futoin/core-php-ri-executor')


class cid_gradle_Test(cid_UTBase):
    @classmethod
    def setUpTool(cls):
        cls._writeFile('build.gradle', '''
defaultTasks 'test_file'
task test_file {
    doLast {
        File tf = file('test_file.txt')
        tf.text = 'Yes'
    }
}
''')
        
    def test10_build( self ):
        self._call_citool( [ 'tool', 'build', self.TOOL_NAME ] )

        with open('test_file.txt', 'r') as f:
            res = f.readlines()
            res.index('Yes')


class cid_grunt_Test(cid_UTBase):
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
        
        
    def test10_build( self ):
        self._call_citool( [ 'tool', 'prepare', 'npm' ] )
        self._call_citool( [ 'tool', 'build', self.TOOL_NAME ] )

        with open('test_file.txt', 'r') as f:
            res = f.readlines()
            res.index('Yes')



class cid_gulp_Test(cid_UTBase):
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
        
        
    def test10_build( self ):
        self._call_citool( [ 'tool', 'prepare', 'npm' ] )
        self._call_citool( [ 'tool', 'build', self.TOOL_NAME ] )

        with open('test_file.txt', 'r') as f:
            res = f.readlines()
            res.index('Yes')


class cid_make_Test(cid_UTBase):
    @classmethod
    def setUpTool(cls):
        cls._writeFile('Makefile', '''
sometarget:
\techo Yes > test_file.txt
''')
        
    def test10_build( self ):
        self._call_citool( [ 'tool', 'build', self.TOOL_NAME ] )
        
        with open('test_file.txt', 'r') as f:
            res = f.readlines()
            res.index('Yes\n')


class cid_maven_Test(cid_UTBase):
    @classmethod
    def setUpTool(cls):
        cls._call_citool( [
            'tool', 'exec', cls.TOOL_NAME, '--',
            'archetype:generate', '-DgroupId=com.mycompany.app',
            '-DartifactId=my-app', '-DarchetypeArtifactId=maven-archetype-quickstart',
            '-DinteractiveMode=false',
        ] )
        
    def test10_build( self ):
        os.chdir( os.path.join(self.TEST_DIR, 'my-app') )
        self._call_citool( [ 'tool', 'build', self.TOOL_NAME ] )
        assert os.path.exists('target')

    def test20_package( self ):
        os.chdir( os.path.join(self.TEST_DIR, 'my-app') )
        self._call_citool( [ 'tool', 'package', self.TOOL_NAME ] )
        assert os.path.exists('target/my-app-1.0-SNAPSHOT.jar')


class cid_npm_Test(cid_UTBase):
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
        
    def test10_prepare( self ):
        self._call_citool( [ 'tool', 'prepare', self.TOOL_NAME ] )
        assert os.path.exists('node_modules/futoin-asyncsteps')
        assert os.path.exists('node_modules/futoin-executor')

    def test20_package( self ):
        self._call_citool( [ 'tool', 'package', self.TOOL_NAME ] )
        assert os.path.exists('node_modules/futoin-asyncsteps')
        assert not os.path.exists('node_modules/futoin-executor')


class cid_pip_Test(cid_UTBase):
    @classmethod
    def setUpTool(cls):
        cls._writeFile('requirements.txt', '''
nose==1.3.7
''')
        
    def test10_prepare( self ):
        self._call_citool( [ 'tool', 'prepare', self.TOOL_NAME ] )
        
        with open('req.txt', 'w') as f:
            self._call_citool( [ 'tool', 'exec', self.TOOL_NAME, '--', 'freeze' ], stdout=f )
            
        with open('req.txt', 'r') as f:
            res = f.readlines()
            res.index('nose==1.3.7\n')

class cid_puppet_Test(cid_UTBase):
    @classmethod
    def setUpTool(cls):
        cls._writeJSON('metadata.json', {
  "name": "futoin-cidpuppettest",
  "version": "0.0.1",
  "summary": "Futoin CID Puppet Test",
})
        
    def test10_build( self ):
        self._call_citool( [ 'tool', 'build', self.TOOL_NAME ] )
        assert os.path.exists('pkg')
        
    def test20_package( self ):
        self._call_citool( [ 'tool', 'package', self.TOOL_NAME ] )
        assert os.path.exists('pkg/futoin-cidpuppettest-0.0.1.tar.gz')


class cid_setuptools_Test(cid_UTBase):
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
        
    def test10_build( self ):
        self._call_citool( [ 'tool', 'build', self.TOOL_NAME ] )
        assert os.path.exists('dist/futoin_cid_testapp-0.0.1-py2.py3-none-any.whl')
        assert os.path.exists('dist/futoin-cid-testapp-0.0.1.tar.gz')
