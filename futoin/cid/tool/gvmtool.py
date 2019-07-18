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


class gvmTool(BashToolMixIn, CurlToolMixIn, RunEnvTool):
    """Go Version Manager.

Home: https://github.com/moovweb/gvm
"""
    __slots__ = ()

    GVM_VERSION_DEFAULT = 'master'
    GVM_INSTALLER_DEFAULT = 'https://raw.githubusercontent.com/moovweb/gvm/master/binscripts/gvm-installer'

    def getDeps(self):
        return (
            ['git', 'hg', 'make', 'binutils'] +
            BashToolMixIn.getDeps(self) +
            CurlToolMixIn.getDeps(self))

    def _installTool(self, env):
        self._install.deb(['bison', 'gcc', 'build-essential'])
        self._install.rpm(['bison', 'gcc', 'glibc-devel'])
        self._install.emergeDepsOnly(['dev-lang/go'])
        self._install.pacman(['bison', 'gcc', 'glibc', ])
        self._install.apk('bison')
        self._builddep.essential()

        gvm_installer = self._callCurl(env, [env['gvmInstaller']])
        self._callBash(
            env,
            input=gvm_installer,
            suppress_fail=True)  # error when Go is not yet installed

    def _updateTool(self, env):
        self._installTool(env)

    def uninstallTool(self, env):
        gvm_dir = env['gvmDir']
        self._pathutil.rmTree(gvm_dir)
        self._have_tool = False

    def envNames(self):
        return ['gvmDir', 'gvmInstaller']

    def initEnv(self, env):
        ospath = self._ospath
        os = self._os
        environ = self._environ
        gvm_dir = ospath.join(environ['HOME'], '.gvm')
        gvm_dir = env.setdefault('gvmDir', gvm_dir)
        environ['GVM_DEST'] = ospath.dirname(gvm_dir)
        environ['GVM_NAME'] = ospath.basename(gvm_dir)
        environ['GVM_NO_UPDATE_PROFILE'] = '1'

        env.setdefault('gvmVer', self.GVM_VERSION_DEFAULT)
        env.setdefault('gvmInstaller', self.GVM_INSTALLER_DEFAULT)

        env_init = ospath.join(gvm_dir, 'scripts', 'gvm')
        env['gvmInit'] = env_init

        self._have_tool = ospath.exists(env_init)

    def onExec(self, env, args, replace=True):
        cmd = '. {0} && gvm {1}'.format(
            env['gvmInit'], self._ext.subprocess.list2cmdline(args))
        self._callBashInteractive(env, cmd, replace=replace)
