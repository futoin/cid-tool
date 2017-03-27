
from ..buildtool import BuildTool
from ..testtool import TestTool
from .sdkmantoolmixin import SdkmanToolMixIn

class mavenTool( SdkmanToolMixIn, BuildTool, TestTool ):
    def autoDetect( self, config ) :
        return self._autoDetectByCfg(
                config,
                [ 'pom.xml' ]
        )
    
    def _binName( self ):
        return 'mvn'
    
    def onBuild( self, config ):
        self._callExternal( [ config['env']['mavenBin'], 'compile' ] )
        
    def onPackage( self, config ):
        self._callExternal( [ config['env']['mavenBin'], 'package' ] )

    def onCheck( self, config ):
        self._callExternal( [ config['env']['mavenBin'], 'test' ] )

            