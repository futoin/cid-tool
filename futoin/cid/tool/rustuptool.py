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
from .bashtoolmixin import BashToolMixIn
from .curltoolmixin import CurlToolMixIn


class rustupTool(BashToolMixIn, CurlToolMixIn, RunEnvTool):
    """rustup is an installer for the systems programming language Rust.

Home: https://www.rustup.rs/
"""
    __slots__ = ()

    INSTALLER_DEFAULT = 'https://sh.rustup.rs'

    def getDeps(self):
        return (
            BashToolMixIn.getDeps(self) +
            CurlToolMixIn.getDeps(self))

    def _installTool(self, env):
        if self._detect.isAlpineLinux():
            self._warn('Unfortunately, rustup does not support musl libc yet')

        installer = self._callCurl(env, [env['rustupInstaller']])

        self._callBash(
            env,
            bash_args=['--', '-y', '--no-modify-path'],
            input=installer)

    def _updateTool(self, env):
        self._executil.callExternal([
            env['rustupBin'], 'self', 'update'
        ])

    def uninstallTool(self, env):
        ospath = self._ospath

        for v in ['rustupDir', 'cargoDir']:
            dir = env[v]
            self._pathutil.rmTree(dir)

        self._have_tool = False

    def envNames(self):
        return ['rustupBin', 'rustupDir', 'rustupInstaller']

    def initEnv(self, env):
        ospath = self._ospath
        environ = self._environ
        dir = ospath.join(environ['HOME'], '.multirust')
        dir = environ.setdefault('RUSTUP_HOME', dir)
        cargo_dir = ospath.join(environ['HOME'], '.cargo')
        cargo_dir = environ.setdefault('CARGO_HOME', cargo_dir)

        dir = env.setdefault('rustupDir', dir)
        cargo_dir = env.setdefault('cargoDir', cargo_dir)

        environ['RUSTUP_HOME'] = dir
        environ['CARGO_HOME'] = cargo_dir

        env.setdefault('rustupInstaller', self.INSTALLER_DEFAULT)

        bin_dir = ospath.join(cargo_dir, 'bin')
        self._pathutil.addBinPath(bin_dir, True)

        if ospath.exists(ospath.join(bin_dir, 'rustup')):
            super(rustupTool, self).initEnv(env)
