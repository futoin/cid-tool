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
from .npmtoolmixin import NpmToolMixIn


class yarnTool(NpmToolMixIn, BuildTool):
    """YARN: fast, reliable, and secure dependency management.

Home: https://yarnpkg.com

Note: auto-detected only if yarn.lock is present
"""
    __slots__ = ()

    def getOrder(self):
        # required to run before other npm-based tools
        return -10

    def autoDetectFiles(self):
        return 'yarn.lock'

    def onPrepare(self, config):
        node_env = self._environ['NODE_ENV']

        try:
            self._environ['NODE_ENV'] = 'development'
            yarnBin = config['env']['yarnBin']
            self._executil.callExternal(
                [yarnBin, 'install', '--production=false'])
        finally:
            self._environ['NODE_ENV'] = node_env

    def onPackage(self, config):
        if not self._isDefaultPackage(config):
            return

        yarnBin = config['env']['yarnBin']
        cmd = [yarnBin, 'install', '--production']
        self._executil.callMeaningful(cmd)
