
from ..buildtool import BuildTool
from .sdkmantoolmixin import SdkmanToolMixIn


class antTool(SdkmanToolMixIn, BuildTool):
    """Ant build tool for Java applications.

Home: http://ant.apache.org/

The tool assumes the following targets: clean, compile, jar, run

Ant is setup through SDKMan!

Note: If detected Java version is less than 8 then Ant 1.9.8 is used.

Build targets:
    prepare -> clean
    build -> compile
    package -> jar
Override targets with .config.toolTune.

"""

    def autoDetectFiles(self):
        return ['build.xml']

    def initEnv(self, env):
        if self._javaVersion(env) < 8:
            env['antVer'] = '1.9.8'

        super(antTool, self).initEnv(env)

    def onPrepare(self, config):
        target = self._getTune(config, 'prepare', 'clean')
        self._callExternal([config['env']['antBin'], target])

    def onBuild(self, config):
        target = self._getTune(config, 'build', 'compile')
        self._callExternal([config['env']['antBin'], target])

    def onPackage(self, config):
        target = self._getTune(config, 'package', 'jar')
        self._callExternal([config['env']['antBin'], target])

        self._addPackageFiles(config, 'build/jar/*.jar')

    def onRunDev(self, config):
        self._callExternal([config['env']['antBin'], 'run'])
