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


class rvmTool(BashToolMixIn, CurlToolMixIn, RunEnvTool):
    """Ruby Version Manager.

Home: https://rvm.io/

Stable RVM is used by default.
"""
    __slots__ = ()

    RVM_LATEST = 'stable'
    RVM_GPG_KEYS = [
        '409B6B1796C275462A1703113804BB82D39DC0E3',
        '7D2BAF1CF37B13E2069D6956105BD0E739499BDB',
    ]
    RVM_GET = 'https://get.rvm.io'

    def getDeps(self):
        return (
            ['gpg', 'tar', 'gzip'] +
            BashToolMixIn.getDeps(self) +
            CurlToolMixIn.getDeps(self))

    def ensureGpgKeys(self, env):
        rvm_gpg_keys = env.get('rvmGpgKeys', '')

        if rvm_gpg_keys != '':
            rvm_gpg_keys = rvm_gpg_keys.split(' ')
        else:
            rvm_gpg_keys = self.RVM_GPG_KEYS

        self._executil.callExternal([
            env['gpgBin'], '--keyserver', env['gpgKeyServer'],
            '--recv-keys'] + rvm_gpg_keys,
            suppress_fail=True)

    def _installTool(self, env):
        self.ensureGpgKeys(env)

        rvm_dir = env['rvmDir']
        rvm_get = env.get('rvmGet', self.RVM_GET)

        environ = self._environ
        environ['rvm_user_install_flag'] = '1'
        environ['rvm_auto_dotfiles_flag'] = '0'

        installer = self._callCurl(env, [rvm_get])

        # AlpineLinux - required for uninstall
        self._install.apk('procps')

        self._callBash(
            env,
            bash_args=['--', env['rvmVer'], '--path', rvm_dir],
            input=installer)

    def _updateTool(self, env):
        self._executil.callExternal([env['rvmBin'], 'get', env['rvmVer']])

    def uninstallTool(self, env):
        try:
            self._executil.callExternal([env['rvmBin'], 'implode', '--force'])
        except:
            pass

        rvm_dir = env['rvmDir']
        self._pathutil.rmTree(rvm_dir)
        self._have_tool = False

    def envNames(self):
        return ['rvmVer', 'rvmDir', 'rvmBin', 'rvmGet', 'rvmGpgKey']

    def initEnv(self, env):
        ospath = self._ospath
        environ = self._environ

        for v in ['rvm_path', 'rvm_bin_path', 'rvm_prefix', 'rvm_version']:
            try:
                del environ[v]
            except:
                pass

        env.setdefault('rvmVer', self.RVM_LATEST)
        rvm_dir = ospath.join(environ['HOME'], '.rvm')
        rvm_dir = env.setdefault('rvmDir', rvm_dir)
        rvm_bin_dir = ospath.join(rvm_dir, 'bin')
        rvm_bin = env['rvmBin'] = ospath.join(rvm_bin_dir, 'rvm')
        env['rvmInit'] = ospath.join(rvm_dir, 'scripts', 'rvm')
        self._have_tool = ospath.exists(rvm_bin)
