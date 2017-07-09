
from ..buildtool import BuildTool


class cmakeTool(BuildTool):
    """Build, Test and Package Your Software With CMake.

Home: https://cmake.org/

CMake creates a build folder and does all processing in it.
Build folder is configurable through cmakeBuildDir env.
"""
    __slots__ = ()

    def getOrder(self):
        return -10

    def autoDetectFiles(self):
        return 'CMakeLists.txt'

    def envNames(self):
        return ['cmakeBin', 'cmakeBuildDir']

    def _installTool(self, env):
        self._install.deb(['build-essential'])
        self._install.rpm(['gcc', 'gcc-c++'])
        self._install.pacman(['gcc'])
        self._builddep.essential()

        self._install.debrpm(['cmake'])
        self._install.emerge(['dev-util/cmake'])
        self._install.pacman(['cmake'])
        self._install.apk(['cmake'])
        self._install.brew('cmake')

    def initEnv(self, env):
        env.setdefault('cmakeBuildDir', 'build')
        super(cmakeTool, self).initEnv(env)

    def onPrepare(self, config):
        build_dir = config['env']['cmakeBuildDir']
        self._pathutil.rmTree(build_dir)

    def onBuild(self, config):
        ospath = self._ospath
        os = self._os
        build_dir = config['env']['cmakeBuildDir']

        if ospath.exists(build_dir):
            self._executil.callExternal([config['env']['cmakeBin'], build_dir])
        else:
            os.mkdir(build_dir)
            os.chdir(build_dir)
            self._executil.callExternal(
                [config['env']['cmakeBin'], config['wcDir']])
            os.chdir(config['wcDir'])

        self._executil.callExternal(
            [config['env']['cmakeBin'], '--build', build_dir])
