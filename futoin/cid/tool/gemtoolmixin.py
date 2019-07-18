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

from ..subtool import SubTool


class GemToolMixIn(SubTool):
    __slots__ = ()

    def getDeps(self):
        return ['gem', 'ruby']

    def _gemName(self):
        return self._name

    def _installTool(self, env):
        if self._detect.isExternalToolsSetup(env):
            self._executil.externalSetup(env, ['build-dep', 'ruby'])
        else:
            self._builddep.require(env, 'ruby')

        ver = env.get(self._name + 'Ver', None)
        version_arg = []

        if ver:
            version_arg = ['--version', ver]

        self._executil.callExternal([env['gemBin'], 'install', self._gemName(
        )] + env['gemInstallArgs'].split(' ') + version_arg)

    def installTool(self, env):
        if not self._have_tool:
            if self._detect.isDisabledToolsSetup(env):
                self._errorExit(
                    'Tool "{0}" must be installed externally (env config)'.format(self._name))
            else:
                self._warn(
                    'Auto-installing required "{0}" tool'.format(self._name))
                self._installTool(env)

            self.initEnv(env)

            if not self._have_tool:
                self._errorExit('Failed to install "{0}"'.format(self._name))

    def _updateTool(self, env):
        if env.get(self._name + 'Ver', None):
            self._installTool(env)
        else:
            self._executil.callExternal(
                [env['gemBin'], 'update', self._gemName()] + env['gemInstallArgs'].split(' '))

    def updateTool(self, env):
        if self._detect.isDisabledToolsSetup(env):
            self._errorExit(
                'Tool "{0}" must be updated externally (env config)'.format(self._name))
        else:
            self._updateTool(env)

    def uninstallTool(self, env):
        self._executil.callExternal([env['gemBin'], 'uninstall',
                                     '--force', self._gemName()])
        self._have_tool = False
