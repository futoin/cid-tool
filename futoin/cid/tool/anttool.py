
from ..buildtool import BuildTool
from .sdkmantoolmixin import SdkmanToolMixIn

class antTool( SdkmanToolMixIn, BuildTool ):
    def autoDetect( self, config ) :
        return self._autoDetectByCfg(
                config,
                [ 'build.xml' ]
        )
    
    def initEnv( self, env ) :
        if self._javaVersion( env ) < 8:
            env['antVer'] = '1.9.8'

        SdkmanToolMixIn.initEnv(self, env)

    def onPrepare( self, config ):
        self._callExternal( [ config['env']['antBin'], 'clean' ] )
    
    def onBuild( self, config ):
        self._callExternal( [ config['env']['antBin'], 'compile' ] )
        
    def onPackage( self, config ):
        self._callExternal( [ config['env']['antBin'], 'jar' ] )
        
    def onRun( self, config ):
        self._callExternal( [ config['env']['antBin'], 'run' ] )

            