
from ..buildtool import BuildTool
from ..testtool import TestTool
from .sdkmantoolmixin import SdkmanToolMixIn

class sbtTool( SdkmanToolMixIn, BuildTool, TestTool ):
    def autoDetect( self, config ) :
        return self._autoDetectByCfg(
                config,
                [ 'build.sbt' ]
        )
    
    def onPrepare( self, config ):
        self._callExternal( [ config['env']['sbtBin'], 'clean' ] )

    def onBuild( self, config ):
        self._callExternal( [ config['env']['sbtBin'], 'compile' ] )

    def onPackage( self, config ):
        self._callExternal( [ config['env']['sbtBin'], 'package' ] )
            
    def onRun( self, config ):
        self._callExternal( [ config['env']['sbtBin'], 'run' ] )
            
    def onCheck( self, config ):
        self._callExternal( [ config['env']['sbtBin'], 'test' ] )
