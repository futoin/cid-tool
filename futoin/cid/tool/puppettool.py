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
from .gemtoolmixin import GemToolMixIn


class puppetTool(GemToolMixIn, BuildTool):
    """Puppet system automation.

Home: https://puppet.com/

Primary purpose is to support Puppet module development.
"""
    __slots__ = ()

    METADATA_FILE = 'metadata.json'

    def envNames(self):
        return ['puppetVer', 'puppetBin']

    def initEnv(self, env):
        super(puppetTool, self).initEnv(env)
        puppet_ver = env.get('puppetVer', None)

        if self._have_tool and puppet_ver:
            try:
                found_ver = self._executil.callExternal(
                    [env['puppetBin'], '--version'], verbose=False)
                self._have_tool = found_ver.find(puppet_ver) >= 0
            except:
                self._have_tool = False
                del env['puppetBin']

    def autoDetectFiles(self):
        return self.METADATA_FILE

    def loadConfig(self, config):
        content = self._pathutil.loadJSONConfig(self.METADATA_FILE)
        if content is None:
            return

        for f in ('name', 'version'):
            if f in content and f not in config:
                config[f] = content[f]

        config['package'] = ['pkg']

    def updateProjectConfig(self, config, updates):
        def updater(json):
            for f in ('name', 'version'):
                if f in updates:
                    json[f] = updates[f]

        return self._pathutil.updateJSONConfig(self.METADATA_FILE, updater)

    def onPrepare(self, config):
        self._pathutil.rmTree('pkg')

    def onBuild(self, config):
        puppetBin = config['env']['puppetBin']
        cmd = [puppetBin, 'module', 'build']
        self._executil.callMeaningful(cmd)

    def onPackage(self, config):
        package_file = 'pkg/{0}-{1}.tar.gz'.format(
            config['name'],
            config['version']
        )

        if not self._ospath.exists(package_file):
            self._errorExit(
                'Puppet Module built package is missing: ' + package_file)

        self._pathutil.addPackageFiles(config, package_file)
