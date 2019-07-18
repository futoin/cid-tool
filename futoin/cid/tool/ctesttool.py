#
# Copyright 2018-2019 Andrey Galkin <andrey@futoin.org>
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

from ..testtool import TestTool


class ctestTool(TestTool):
    """Build, Test and Package Your Software With CMake.

Home: https://cmake.org/

CTest runs tests in CMake build folder, if any.
"""
    __slots__ = ()

    def autoDetectFiles(self):
        return 'CMakeLists.txt'

    def getDeps(self):
        return ['cmake']

    def envNames(self):
        return ['ctestBin']

    def initEnv(self, env):
        self._environ.setdefault('CTEST_OUTPUT_ON_FAILURE', '1')
        super(ctestTool, self).initEnv(env)

    def onCheck(self, config):
        ospath = self._ospath
        os = self._os
        build_dir = config['env']['cmakeBuildDir']

        if ospath.exists(build_dir):
            os.chdir(build_dir)
            cmd = [config['env']['ctestBin']]
            self._executil.callMeaningful(cmd)
            os.chdir(config['wcDir'])
