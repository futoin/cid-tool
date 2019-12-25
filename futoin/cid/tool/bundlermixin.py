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


class BundlerMixIn(SubTool):
    __slots__ = ()

    def getDeps(self):
        return ['bundler']

    def _gemName(self):
        return self._name

    def _installTool(self, env):
        self._have_tool = True
        tcmd = [env['bundlerBin'], 'add', self._gemName()]
        ver = env.get(self._name + 'Ver')

        if ver:
            tcmd.append('--version={0}'.format(ver))

        try:
            self._executil.callExternal(tcmd, verbose=False)
            # self._executil.callMeaningful(tcmd)
        except Exception as e:
            self._warn(str(e))
            bundlerTools = env.setdefault('bundlerTools', {})
            bundlerTools[self._name] = ver
            return

        cmd = [env['bundlerBin'], 'install']
        self._executil.callExternal(cmd, verbose=False)
        # self._executil.callMeaningful(cmd)

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

    def updateTool(self, env):
        # New version is installed, if not in project
        # Otherwise, the project is responsible  for updates
        self._ensureInstalled(env)

    def initEnv(self, env):
        ospath = self._ospath

        # try newer layout first
        bin_path = ospath.join(
            env['bundlePath'],
            'ruby', '{0}.0'.format(env['rubyVer']),
            'bin', self._name)

        # fallback to legacy
        if not ospath.exists(bin_path):
            bin_path = ospath.join(env['bundlePath'], 'bin', self._name)

        env[self._name + 'Bin'] = bin_path

        if not ospath.exists('Gemfile'):
            # Fake to workaround being required outside of project root (e.g. deployment home)
            self._have_tool = True
            return

        self._have_tool = self._have_tool or ospath.exists(bin_path)

    def onRun(self, config, svc, args):
        env = config['env']
        self._ensureInstalled(env)
        self._executil.callInteractive([
            env['bundlerBin'], 'exec', self._gemName(), '--', svc['path']
        ] + args)

    def _ensureInstalled(self, env):
        bin_path = env.get(self._name + 'Bin')

        if not bin_path or not self._ospath.exists(bin_path):
            self._have_tool = False
            self.installTool(env)
