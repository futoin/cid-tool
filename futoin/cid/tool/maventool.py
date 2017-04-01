
from ..buildtool import BuildTool
from ..testtool import TestTool
from .sdkmantoolmixin import SdkmanToolMixIn

class mavenTool( SdkmanToolMixIn, BuildTool, TestTool ):
    """Apache Maven is a software project management and comprehension tool.

Home: https://maven.apache.org/

Auto-detected based on pom.xml

Expects clean, compile, package and test targets.

Build targets:
    prepare -> clean
    build -> compile
    package -> package
    check -> test
Override targets with .config.toolTune.

Requires Java >= 7.
"""
    _MIN_JAVA = '7'
    
    def autoDetect( self, config ) :
        return self._autoDetectByCfg(
                config,
                [ 'pom.xml' ]
        )
    
    def _binName( self ):
        return 'mvn'

    def onPrepare( self, config ):
        target = self._getTune(config, 'prepare', 'clean')
        self._callExternal( [ config['env']['mavenBin'], target ] )
    
    def onBuild( self, config ):
        target = self._getTune(config, 'build', 'compile')
        self._callExternal( [ config['env']['mavenBin'], target ] )
        
    def onPackage( self, config ):
        target = self._getTune(config, 'package', 'package')
        self._callExternal( [ config['env']['mavenBin'], target ] )

    def onCheck( self, config ):
        target = self._getTune(config, 'check', 'test')
        self._callExternal( [ config['env']['mavenBin'], target ] )

            