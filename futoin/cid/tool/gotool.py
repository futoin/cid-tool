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

from ..runtimetool import RuntimeTool
from .bashtoolmixin import BashToolMixIn


class goTool(BashToolMixIn, RuntimeTool):
    """The Go Programming Language

Home: https://golang.org/

All versions are installed through GVM.

Only binary releases of Golang are supported for installation
through CID, but you can install source releases through
"cte gvm install sourcetag".
"""
    __slots__ = ()

    def getDeps(self):
        return ['gvm', 'bash', 'binutils', 'gcc']

    def getVersionParts(self):
        return 3

    def _installTool(self, env):
        if self._detect.isAlpineLinux():
            self._install.apkCommunity()
            self._install.apk('go')
            return

        # in case GVM is already installed without these deps
        self._install.deb(['bison', 'build-essential'])
        self._install.rpm(['bison', 'glibc-devel'])
        self._install.emergeDepsOnly(['dev-lang/go'])
        self._install.pacman(['bison', 'glibc', ])
        self._install.apk('bison')
        self._builddep.essential()

        self._callBash(env,
                       'source {0} && gvm install go{1} --binary'
                       .format(env['gvmInit'], env['goVer'])
                       )

    def _updateTool(self, env):
        self._installTool(env)

    def uninstallTool(self, env):
        self._callBash(env,
                       'source {0} && gvm uninstall go{1}'
                       .format(env['gvmInit'], env['goVer'])
                       )
        self._have_tool = False

    def envNames(self):
        return ['goVer', 'goBin']

    def initEnv(self, env):
        if self._detect.isAlpineLinux():
            super(goTool, self).initEnv(env)
            return

        if not env.get('goVer', None):
            try:
                cmd = 'source {0} && gvm listall'.format(env['gvmInit'])
                ver_list = self._callBash(env, cmd, verbose=False)
                ver_list = ver_list.split("\n")

                rex = self._ext.re.compile('^go[0-9]+\.[0-9]+(\.[0-9]+)?$')

                ver_list = [v.strip() for v in ver_list]
                ver_list = filter(lambda x: x and rex.match(x), ver_list)

                ver = self._versionutil.latest(list(ver_list))
                env['goVer'] = ver.replace('go', '')
            except Exception as e:
                self._warn(str(e))
                return

        ver = env['goVer']

        try:
            env_to_set = self._callBash(env,
                                        'source {0} && \
                gvm use {1} >/dev/null && \
                env | egrep -i "(gvm|golang)"'.format(env['gvmInit'], ver),
                                        verbose=False
                                        )
        except:
            return

        if env_to_set:
            self._pathutil.updateEnvFromOutput(env_to_set)
            super(goTool, self).initEnv(env)

    def onRun(self, config, svc, args):
        env = config['env']
        self._executil.callInteractive([
            env[self._name + 'Bin'], 'run', svc['path']
        ] + args)
