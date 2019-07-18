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


class gemTool(BuildTool):
    """RubyGems: Find, install, and publish RubyGems.

Home: https://rubygems.org/

If rubyVer is equal to system then gems are installed in
user's folder gemDir.

gemDir is equal to ~/.gem by default.

gemInstallArgs is forcibly set by tool depending on its version.
"""
    __slots__ = ()

    def getDeps(self):
        return ['ruby']

    def uninstallTool(self, env):
        pass

    def envNames(self):
        return ['gemBin', 'gemDir', 'gemInstallArgs']

    def initEnv(self, env):
        ospath = self._ospath
        environ = self._environ
        installArgs = []

        if env['rubyVer'] == self.SYSTEM_VER or env['rubyBinOnly']:
            gemDir = ospath.join(self._pathutil.deployHome(),
                                 '.gem', env['rubyVer'])
            gemDir = env.setdefault('gemDir', gemDir)
            environ['GEM_HOME'] = gemDir
            environ['GEM_PATH'] = gemDir
            environ['GEM_SPEC_CACHE'] = ospath.join(gemDir, 'specs')

            #self._pathutil.addEnvPath('GEM_PATH', gemDir)
            self._pathutil.addBinPath(ospath.join(gemDir, 'bin'), True)
            installArgs += ['--no-user-install', '--no-format-executable']

        super(gemTool, self).initEnv(env)

        if self._have_tool:
            version = self._executil.callExternal(
                [env['gemBin'], '--version'], verbose=False).strip()

            if version >= '2':
                installArgs += ['--no-document']
            else:
                installArgs += ['--no-ri', '--no-rdoc']

            env['gemInstallArgs'] = ' '.join(installArgs)
