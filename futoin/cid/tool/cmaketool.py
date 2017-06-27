
import os

from ..buildtool import BuildTool


class cmakeTool(BuildTool):
    """Build, Test and Package Your Software With CMake.

Home: https://cmake.org/

CMake creates a build folder and does all processing in it.
Build folder is configurable through cmakeBuildDir env.
"""

    def getOrder(self):
        return -10

    def autoDetectFiles(self):
        return 'CMakeLists.txt'

    def envNames(self):
        return ['cmakeBin', 'cmakeBuildDir']

    def _installTool(self, env):
        self._requireDeb(['build-essential'])
        self._requireRpm(['gcc', 'gcc-c++'])
        self._requirePacman(['gcc'])
        self._requireBuildEssential()

        self._requirePackages(['cmake'])
        self._requireEmerge(['dev-util/cmake'])
        self._requirePacman(['cmake'])
        self._requireApk(['cmake'])
        self._requireBrew('cmake')

    def initEnv(self, env):
        env.setdefault('cmakeBuildDir', 'build')
        super(cmakeTool, self).initEnv(env)

    def onPrepare(self, config):
        build_dir = config['env']['cmakeBuildDir']

        if os.path.exists(build_dir):
            self._rmTree(build_dir)

    def onBuild(self, config):
        build_dir = config['env']['cmakeBuildDir']

        if os.path.exists(build_dir):
            self._callExternal([config['env']['cmakeBin'], build_dir])
        else:
            os.mkdir(build_dir)
            os.chdir(build_dir)
            self._callExternal([config['env']['cmakeBin'], config['wcDir']])
            os.chdir(config['wcDir'])

        self._callExternal([config['env']['cmakeBin'], '--build', build_dir])
