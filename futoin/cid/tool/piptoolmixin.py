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


class PipToolMixIn(SubTool):
    __slots__ = ()

    def getDeps(self):
        return ['pip', 'virtualenv']

    def _pipName(self):
        return self._name

    def _installTool(self, env):
        self._builddep.require(env, 'python')

        self._executil.callExternal(
            [env['pipBin'], 'install', '-q', self._pipName()])

    def installTool(self, env):
        if not self._have_tool:
            self._installTool(env)
            self.initEnv(env)

            if not self._have_tool:
                self._errorExit('Failed to install "{0}"'.format(self._name))

    def _updateTool(self, env):
        self._executil.callExternal([env['pipBin'], 'install', '-q',
                                     '--upgrade', self._pipName()])

    def uninstallTool(self, env):
        self._executil.callExternal([env['pipBin'], 'uninstall',
                                     '--yes', '-q', self._pipName()])
        self._have_tool = False

    def initEnv(self, env, bin_name=None):
        name = self._name
        bin_env = name + 'Bin'

        if not env.get(bin_env, None):
            if bin_name is None:
                bin_name = name

            ospath = self._ospath
            tool_path = ospath.join(env['virtualenvDir'], 'bin', bin_name)

            if ospath.exists(tool_path):
                env[bin_env] = tool_path
                self._have_tool = True
        else:
            self._have_tool = True

    def _requirePythonDev(self, env):
        if int(env['pythonVer'].split('.')[0]) == 3:
            self._install.deb(['python3-dev'])
            self._install.zypper(['python3-devel'])
            self._install.yumEPEL()
            self._install.yum(['python34-devel'])
            self._install.pacman(['python'])
            self._install.apk('python3-dev')
        else:
            self._install.deb(['python-dev'])
            self._install.zypper(['python-devel'])
            self._install.yumEPEL()
            self._install.yum(['python-devel'])
            self._install.pacman(['python2'])
            self._install.apk('python2-dev')

        self._install.emergeDepsOnly(['dev-lang/python'])

    def _requirePip(self, env, package):
        self._executil.callExternal([env['pipBin'], 'install', '-q', package])
