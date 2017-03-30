
from ..buildtool import BuildTool
from .sdkmantoolmixin import SdkmanToolMixIn

class antTool( SdkmanToolMixIn, BuildTool ):
    """Ant build tool for Java applications.
    
Home: http://ant.apache.org/

Ant is auto-detected based on build.xml.
The tool assumes the following targets: clean, compile, jar, run

Ant is setup through SDKMan!

Note: If detected Java version is less than 8 then Ant 1.9.8 is used.
"""
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
        
    def onRunDev( self, config ):
        self._callExternal( [ config['env']['antBin'], 'run' ] )

            