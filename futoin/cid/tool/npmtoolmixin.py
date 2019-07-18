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


class NpmToolMixIn(SubTool):
    __slots__ = ()

    def getDeps(self):
        return ['node', 'npm']

    def _npmName(self):
        return self._name

    def _isGlobalNpm(self):
        return self._detect.isAlpineLinux()

    def _installTool(self, env):
        cmd = [env['npmBin'], 'install', '-g', self._npmName()]

        if self._isGlobalNpm():
            self._executil.trySudoCall(cmd + ['--unsafe-perm'])
        else:
            self._executil.callExternal(cmd)

    def _updateTool(self, env):
        cmd = [env['npmBin'], 'update', '-g', self._npmName()]

        if self._isGlobalNpm():
            self._executil.trySudoCall(cmd + ['--unsafe-perm'])
        else:
            self._executil.callExternal(cmd)

    def uninstallTool(self, env):
        cmd = [env['npmBin'], 'uninstall', '-g', self._npmName()]

        if self._isGlobalNpm():
            self._executil.trySudoCall(cmd + ['--unsafe-perm'])
        else:
            self._executil.callExternal(cmd)

        self._have_tool = False

    def initEnv(self, env, bin_name=None):
        name = self._name
        bin_env = name + 'Bin'

        if not env.get(bin_env, None):
            if bin_name is None:
                bin_name = name

            npmBinDir = env.get('npmBinDir', None)

            if npmBinDir:
                tool_path = self._pathutil.safeJoin(npmBinDir, bin_name)

                if self._ospath.exists(tool_path):
                    env[bin_env] = tool_path
                    self._have_tool = True
        else:
            self._have_tool = True
