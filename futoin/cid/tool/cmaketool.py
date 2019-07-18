#
# Copyright 2015-2019 Andrey Galkin <andrey@futoin.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from ..buildtool import BuildTool


class cmakeTool(BuildTool):
    """Build, Test and Package Your Software With CMake.

Home: https://cmake.org/

CMake creates a build folder and does all processing in it.
Build folder is configurable through cmakeBuildDir env.

On release tagging, CMakeLists.txt the following replacements are done:
1. 'VERSION ".*" # AUTO-REPLACE' -> new version
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
        ospath = self._ospath
        os = self._os
        build_dir = config['env']['cmakeBuildDir']
        self._pathutil.rmTree(build_dir)

        os.mkdir(build_dir)
        cmd = [config['env']['cmakeBin'], '-H' +
               config['wcDir'], '-B' + build_dir]
        self._executil.callMeaningful(cmd)

    def onBuild(self, config):
        ospath = self._ospath
        os = self._os
        build_dir = config['env']['cmakeBuildDir']

        if ospath.exists(build_dir):
            cmd = [config['env']['cmakeBin'], build_dir]
            self._executil.callMeaningful(cmd)
        else:
            self.onPrepare(config)

        cmd = [config['env']['cmakeBin'], '--build', build_dir]
        self._executil.callMeaningful(cmd)

    def updateProjectConfig(self, config, updates):
        re = self._ext.re

        def cmake_updater(content):
            if 'version' in updates:
                return re.sub(
                    r'VERSION.*".*".*# AUTO-REPLACE',
                    'VERSION "{0}" # AUTO-REPLACE'.format(updates['version']),
                    content,
                    flags=re.MULTILINE
                )

        return self._pathutil.updateTextFile(
            self.autoDetectFiles(), cmake_updater)
