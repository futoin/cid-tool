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


class bowerTool(NpmToolMixIn, BuildTool):
    """Bower: a package manager for the web.

Home: https://bower.io/
"""
    __slots__ = ()

    BOWER_JSON = 'bower.json'

    def autoDetectFiles(self):
        return self.BOWER_JSON

    def loadConfig(self, config):
        content = self._pathutil.loadJSONConfig(self.BOWER_JSON)
        if content is None:
            return

        f = 'name'
        if f in content and f not in config:
            config[f] = content[f]

    def updateProjectConfig(self, config, updates):
        def updater(json):
            f = 'name'
            if f in updates:
                json[f] = updates[f]

            # version is deprecated
            if 'version' in json:
                del json['version']

        return self._pathutil.updateJSONConfig(self.BOWER_JSON, updater)

    def onPrepare(self, config):
        bowerBin = config['env']['bowerBin']
        self._executil.callExternal([bowerBin, 'install'])

    def onPackage(self, config):
        if not self._isDefaultPackage(config):
            return

        # Bower does not remove dev deps by itself
        self._pathutil.rmTree('bower_components')

        bowerBin = config['env']['bowerBin']
        self._executil.callExternal([bowerBin, 'install', '--production'])
