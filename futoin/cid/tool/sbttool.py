
from ..buildtool import BuildTool
from ..testtool import TestTool
from .sdkmantoolmixin import SdkmanToolMixIn

class sbtTool( SdkmanToolMixIn, BuildTool, TestTool ):
    """The interactive build tool (Scala).
    
Home: http://www.scala-sbt.org/

Auto-detected based on build.sbt

Installed via SDKMan!

First run of SBT may consume a lot of time on post-installation steps.
"""
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
            
    def onRunDev( self, config ):
        self._callExternal( [ config['env']['sbtBin'], 'run' ] )
            
    def onCheck( self, config ):
        self._callExternal( [ config['env']['sbtBin'], 'test' ] )
