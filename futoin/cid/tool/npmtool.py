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
from ..rmstool import RmsTool


class npmTool(BuildTool, RmsTool):
    """npm is the package manager for JavaScript.

Home: https://www.npmjs.com/

In RMS mode support tuning through .toolTune.npm:
    .tag - npm publish --tag
    .access - npm publish --access

Note: it auto-disables, if Yarn tool is detected
"""
    __slots__ = ()

    PACKAGE_JSON = 'package.json'

    def autoDetectFiles(self):
        return self.PACKAGE_JSON

    def getDeps(self):
        return ['node']

    def _isGlobalNpm(self):
        return self._detect.isAlpineLinux()

    def _isYarnInUse(self, config):
        return 'yarn' in config['toolOrder']

    def _installTool(self, env):
        if self._isGlobalNpm():
            if env['nodeVer'] == 'current':
                self._install.apk('nodejs-npm-current')
            else:
                self._install.apk('nodejs-npm')
            return

    def _updateTool(self, env):
        if self._isGlobalNpm():
            return

        self._executil.callExternal([env['npmBin'], 'update', '-g', 'npm'])

    def uninstallTool(self, env):
        pass

    def initEnv(self, env, bin_name=None):
        # prevent extra background processes
        self._environ['NO_UPDATE_NOTIFIER'] = '1'

        super(npmTool, self).initEnv(env, bin_name)

        if self._have_tool:
            env['npmBinDir'] = self._executil.callExternal(
                [env['npmBin'], 'bin', '-g'], verbose=False).strip()

    def loadConfig(self, config):
        content = self._pathutil.loadJSONConfig(self.PACKAGE_JSON)
        if content is None:
            return

        for f in ('name', 'version'):
            if f in content and f not in config:
                config[f] = content[f]

    def updateProjectConfig(self, config, updates):
        def updater(json):
            for f in ('name', 'version'):
                if f in updates:
                    json[f] = updates[f]

        return self._pathutil.updateJSONConfig(self.PACKAGE_JSON, updater)

    def onPrepare(self, config):
        if self._ospath.exists(self.PACKAGE_JSON) and not self._isYarnInUse(config):
            npmBin = config['env']['npmBin']
            cmd = [npmBin, 'install', '--production=false']
            self._executil.callMeaningful(cmd)

    def _npmPackageName(self, config):
        name = config['name'].replace('@', '').replace('/', '-')

        package = '{0}-{1}.tgz'.format(name, config['version'])

        return package

    def onPackage(self, config):
        if not self._isDefaultPackage(config):
            return

        npmBin = config['env']['npmBin']

        if self._ospath.exists(self.PACKAGE_JSON) and not self._isYarnInUse(config):
            #self._executil.callExternal([npmBin, 'prune', '--production'])
            # https://github.com/npm/npm/issues/17781
            self._pathutil.rmTree('node_modules')
            cmd = [npmBin, 'install', '--production']
            self._executil.callMeaningful(cmd)

        if config.get('rms', None) == self._name:
            cmd = [npmBin, 'pack']
            self._executil.callMeaningful(cmd)
            package = self._npmPackageName(config)
            self._pathutil.addPackageFiles(config, package)

    def rmsUpload(self, config, rms_pool, package_list):
        ospath = self._ospath
        package = self._npmPackageName(config)

        if (len(package_list) == 1 and
                ospath.basename(package_list[0]) == package):
            self._warn('Workaround for known "npm publish" tarball issues')
            self._pathutil.rmTree(package)
        else:
            self._errorExit('Unexpected package list: {0}'
                            .format(package_list))

        npmBin = config['env']['npmBin']
        cmd = [npmBin, 'publish']

        tune = config.get('toolTune', {}).get('npm', {})

        if 'tag' in tune:
            cmd += ['--tag', tune['tag']]

        if 'access' in tune:
            cmd += ['--access', tune['access']]

        self._executil.callMeaningful(cmd)

    def rmsPoolList(self, config):
        return [
            'registry',
        ]
