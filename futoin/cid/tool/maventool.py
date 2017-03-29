
from ..buildtool import BuildTool
from ..testtool import TestTool
from .sdkmantoolmixin import SdkmanToolMixIn

class mavenTool( SdkmanToolMixIn, BuildTool, TestTool ):
    """Apache Maven is a software project management and comprehension tool.

Home: https://maven.apache.org/

Auto-detected based on pom.xml

Expects clean, compile, package and test targets.
"""    
    def autoDetect( self, config ) :
        return self._autoDetectByCfg(
                config,
                [ 'pom.xml' ]
        )
    
    def _binName( self ):
        return 'mvn'

    def onPrepare( self, config ):
        self._callExternal( [ config['env']['mavenBin'], 'clean' ] )
    
    def onBuild( self, config ):
        self._callExternal( [ config['env']['mavenBin'], 'compile' ] )
        
    def onPackage( self, config ):
        self._callExternal( [ config['env']['mavenBin'], 'package' ] )

    def onCheck( self, config ):
        self._callExternal( [ config['env']['mavenBin'], 'test' ] )

            