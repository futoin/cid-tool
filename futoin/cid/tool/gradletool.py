
from ..buildtool import BuildTool
from .sdkmantoolmixin import SdkmanToolMixIn


class gradleTool(SdkmanToolMixIn, BuildTool):
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
    __slots__ = ()

    def _minJava(self):
        return '7'

    def autoDetectFiles(self):
        return 'build.gradle'

    def envDeps(self, env):
        super(gradleTool, self).envDeps(env)

        gradlew_prop = 'gradle/wrapper/gradle-wrapper.properties'

        if self._ospath.exists(gradlew_prop):
            with open(gradlew_prop, 'r') as f:
                props = f.read()
                env['gradleVer'] = self._ext.re.search(
                    'gradle-([0-9.]+)-bin.zip', props).group(1)

    def onPrepare(self, config):
        target = self._getTune(config, 'prepare', 'clean')
        cmd = [config['env']['gradleBin'],
               '-q', '--no-daemon', target]
        self._executil.callMeaningful(cmd)

    def onBuild(self, config):
        target = self._getTune(config, 'build')

        if target:
            args = [target]
        else:
            args = []

        cmd = [config['env']['gradleBin'],
               '-q', '--no-daemon'] + args
        self._executil.callMeaningful(cmd)

    def onPackage(self, config):
        target = self._getTune(config, 'package', 'dists')
        cmd = [config['env']['gradleBin'],
               '-q', '--no-daemon', target]
        self._executil.callMeaningful(cmd)

        packageGlob = self._getTune(config, 'packageGlob', 'build/libs/*.jar')
        self._pathutil.addPackageFiles(config, packageGlob)
