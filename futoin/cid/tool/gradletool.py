
from ..buildtool import BuildTool
from .sdkmantoolmixin import SdkmanToolMixIn

class gradleTool( SdkmanToolMixIn, BuildTool ):
    def autoDetect( self, config ) :
        return self._autoDetectByCfg(
                config,
                [ 'build.gradle' ]
        )
    
    def onBuild( self, config ):
        self._callExternal( [ config['env']['gradleBin'], '-q', '--no-daemon' ] )
            