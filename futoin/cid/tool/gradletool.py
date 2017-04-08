
from ..buildtool import BuildTool
from .sdkmantoolmixin import SdkmanToolMixIn

class gradleTool( SdkmanToolMixIn, BuildTool ):
    """Gradle Build Tool.

Home: https://gradle.org/

Build targets:
    prepare -> clean
    build -> <default> without explicit target
    package -> dists
    packageGlob -> '*.jar'
Override targets with .config.toolTune.

Requires Java >= 7.
"""
    _MIN_JAVA = '7'
    
    def autoDetectFiles( self ) :
        return 'build.gradle'

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
        
        packageGlob = self._getTune(config, 'packageGlob', '*.jar')
        self._addPackageFiles(config, packageGlob)
            