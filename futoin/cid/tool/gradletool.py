
from ..buildtool import BuildTool
from .sdkmantoolmixin import SdkmanToolMixIn

class gradleTool( SdkmanToolMixIn, BuildTool ):
    """Gradle Build Tool.

Home: https://gradle.org/

Auto-detected based on build.gradle.
"""    
    def autoDetect( self, config ) :
        return self._autoDetectByCfg(
                config,
                [ 'build.gradle' ]
        )

    def onPrepare( self, config ):
        self._callExternal( [ config['env']['gradleBin'], '-q', '--no-daemon', 'clean' ] )
    
    def onBuild( self, config ):
        self._callExternal( [ config['env']['gradleBin'], '-q', '--no-daemon' ] )

    def onPackage( self, config ):
        self._callExternal( [ config['env']['gradleBin'], '-q', '--no-daemon', 'dists' ] )
            