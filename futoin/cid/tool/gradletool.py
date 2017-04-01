
from ..buildtool import BuildTool
from .sdkmantoolmixin import SdkmanToolMixIn

class gradleTool( SdkmanToolMixIn, BuildTool ):
    """Gradle Build Tool.

Home: https://gradle.org/

Auto-detected based on build.gradle.

Build targets:
    prepare -> clean
    build -> <default> without explicit target
    package -> dists
Override targets with .config.toolTune.

Requires Java >= 7.
"""
    _MIN_JAVA = '7'
    
    def autoDetect( self, config ) :
        return self._autoDetectByCfg(
                config,
                [ 'build.gradle' ]
        )

    def onPrepare( self, config ):
        target = self._getTune(config, 'prepare', 'clean')
        self._callExternal( [ config['env']['gradleBin'], '-q', '--no-daemon', target ] )
    
    def onBuild( self, config ):
        target = self._getTune(config, 'build')
        
        if target:
            args = [target]
        else:
            args = []
            
        self._callExternal( [ config['env']['gradleBin'], '-q', '--no-daemon' ] + args )

    def onPackage( self, config ):
        target = self._getTune(config, 'package', 'dists')
        self._callExternal( [ config['env']['gradleBin'], '-q', '--no-daemon', target ] )
            