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
from ..runenvtool import RunEnvTool
from .piptoolmixin import PipToolMixIn


class dockercomposeTool(PipToolMixIn, BuildTool, RunEnvTool):
    """Compose is a tool for defining and running multi-container Docker applications.

Home: https://docs.docker.com/compose/

Experimental support.
"""
    __slots__ = ()

    def autoDetectFiles(self):
        return ['docker-compose.yml', 'docker-compose.yaml']

    def getDeps(self):
        return ['pip', 'docker']

    def getOrder(self):
        return 20

    def _pipName(self):
        return 'docker-compose'

    def _installTool(self, env):
        self._requirePythonDev(env)
        super(dockercomposeTool, self)._installTool(env)

    def onBuild(self, config):
        cmd = [config['env']['dockercomposeBin'], 'build']
        self._executil.callMeaningful(cmd)

    def onPackage(self, config):
        cmd = [config['env']['dockercomposeBin'], 'bundle']
        self._executil.callMeaningful(cmd)

    def initEnv(self, env):
        super(dockercomposeTool, self).initEnv(env, 'docker-compose')
