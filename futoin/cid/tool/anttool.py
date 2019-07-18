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
    __slots__ = ()

    def autoDetectFiles(self):
        return ['build.xml']

    def initEnv(self, env):
        if self._javaVersion(env) < 8:
            env['antVer'] = '1.9.8'

        super(antTool, self).initEnv(env)

    def _callAnt(self, config, target):
        cmd = [config['env']['antBin'], target]
        self._executil.callMeaningful(cmd)

    def onPrepare(self, config):
        target = self._getTune(config, 'prepare', 'clean')
        self._callAnt(config, target)

    def onBuild(self, config):
        target = self._getTune(config, 'build', 'compile')
        self._callAnt(config, target)

    def onPackage(self, config):
        target = self._getTune(config, 'package', 'jar')
        self._callAnt(config, target)

        self._pathutil.addPackageFiles(config, 'build/jar/*.jar')

    def onRunDev(self, config):
        self._callAnt(config, 'run')
