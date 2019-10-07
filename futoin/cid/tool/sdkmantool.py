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


class sdkmanTool(BashToolMixIn, CurlToolMixIn, RunEnvTool):
    """SDK Man for Java.

Home: http://sdkman.io/
"""
    __slots__ = ()

    def getDeps(self):
        return (
            ['unzip', 'zip'] +
            BashToolMixIn.getDeps(self) +
            CurlToolMixIn.getDeps(self))

    def envNames(self):
        return ['sdkmanDir', 'sdkmanGet']

    def _installTool(self, env):
        dir = env['sdkmanDir']
        get = env.get('sdkmanGet', 'https://get.sdkman.io')

        installer = self._callCurl(env, [get])

        environ = self._environ
        environ['SDKMAN_DIR'] = dir
        self._callBash(env, input=installer)
        del environ['SDKMAN_DIR']

    def _updateTool(self, env):
        self._callBash(env,
                       'source {0} && sdk selfupgrade'.format(
                           env['sdkmanInit'])
                       )

    def uninstallTool(self, env):
        dir = env['sdkmanDir']
        self._pathutil.rmTree(dir)
        self._have_tool = False

    def initEnv(self, env):
        ospath = self._ospath
        dir = ospath.join(self._environ['HOME'], '.sdkman')
        dir = env.setdefault('sdkmanDir', dir)
        self._environ['SDKMAN_DIR'] = dir
        env_init = ospath.join(dir, 'bin', 'sdkman-init.sh')
        env['sdkmanInit'] = env_init
        self._have_tool = ospath.exists(env_init)

    def onExec(self, env, args, replace=True):
        cmd = '. {0} && sdk {1}'.format(
            env['sdkmanInit'], self._ext.subprocess.list2cmdline(args))
        self._callBashInteractive(env, cmd, replace=replace)
