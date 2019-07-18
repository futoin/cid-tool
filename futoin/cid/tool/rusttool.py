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

from ..runenvtool import RunEnvTool


class rustTool(RunEnvTool):
    """Rust is a systems programming language.

Home: https://www.rust-lang.org
"""
    __slots__ = ()

    def getDeps(self):
        if self._isGlobalRust():
            return []

        return ['rustup']

    def getVersionParts(self):
        return 3

    def _isGlobalRust(self):
        return self._detect.isAlpineLinux()

    def _installTool(self, env):
        if self._isGlobalRust():
            self._install.apk('rust')
            return

        self._executil.callExternal([
            env['rustupBin'], 'toolchain', 'install', env['rustVer']
        ])

    def _updateTool(self, env):
        self._installTool(env)

    def uninstallTool(self, env):
        if self._isGlobalRust():
            return

        self._executil.callExternal([
            env['rustupBin'], 'toolchain', 'uninstall', env['rustVer']
        ])
        self._have_tool = False

    def envNames(self):
        return ['rustBin', 'rustVer']

    def initEnv(self, env):
        if not self._isGlobalRust():
            ver = env.setdefault('rustVer', 'stable')
            self._environ['RUSTUP_TOOLCHAIN'] = ver

            try:
                res = self._executil.callExternal([
                    env['rustupBin'], 'which', 'rustc'
                ], verbose=False)
            except:
                return

        super(rustTool, self).initEnv(env, 'rustc')
