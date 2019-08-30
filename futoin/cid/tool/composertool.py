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
from .curltoolmixin import CurlToolMixIn


class composerTool(CurlToolMixIn, BuildTool):
    """Dependency Manager for PHP.

Home: https://getcomposer.org/

Composer is installed in composerDir as single Phar with "composer" name without
extension.
composerDir is equal to user's ~/bin/ folder by default.
"""
    __slots__ = ()

    COMPOSER_JSON = 'composer.json'

    def _installTool(self, env):
        composer_dir = env['composerDir']
        php_bin = env['phpBin']
        composer_get = env.get(
            'composerGet', 'https://getcomposer.org/installer')

        composer_installer = self._callCurl(
            env, [composer_get], binary_output=True)

        if not self._ospath.exists(composer_dir):
            self._os.makedirs(composer_dir)

        self._phputil.installExtensions(env, [
            'phar',
            'openssl',
            'json',
            'filter',
            'hash',
            'mbstring',
        ])
        self._phputil.installExtensions(env, [
            'zip',
            'apcu',
            'zlib',
        ], True)

        self._executil.callExternal(
            [
                php_bin, '--',
                '--install-dir=' + composer_dir,
                '--filename=composer'
            ],
            input=composer_installer,
            binary_input=True)

    def _updateTool(self, env):
        self._executil.callExternal([env['composerBin'], 'self-update'])

    def uninstallTool(self, env):
        self._os.remove(env['composerBin'])
        self._have_tool = False

    def envNames(self):
        return ['composerDir', 'composerBin', 'composerGet']

    def initEnv(self, env):
        ospath = self._ospath
        bin_dir = env['binDir']
        composer_dir = env.setdefault('composerDir', bin_dir)
        composer_bin = env.setdefault(
            'composerBin', ospath.join(composer_dir, 'composer'))

        self._pathutil.addBinPath(composer_dir)

        self._have_tool = ospath.exists(composer_bin)

    def autoDetectFiles(self):
        return self.COMPOSER_JSON

    def getDeps(self):
        return ['php', 'git'] + CurlToolMixIn.getDeps(self)

    def loadConfig(self, config):
        content = self._pathutil.loadJSONConfig(self.COMPOSER_JSON)
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

        return self._pathutil.updateJSONConfig(self.COMPOSER_JSON, updater, indent=4)

    def onPrepare(self, config):
        composerBin = config['env']['composerBin']
        cmd = [composerBin, 'install']
        self._executil.callMeaningful(cmd)

    def onPackage(self, config):
        if not self._isDefaultPackage(config):
            return

        composerBin = config['env']['composerBin']
        cmd = [composerBin, 'install', '--no-dev', '--no-scripts']
        self._executil.callMeaningful(cmd)
