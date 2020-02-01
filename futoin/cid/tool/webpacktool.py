#
# Copyright 2015-2020 Andrey Galkin <andrey@futoin.org>
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
from .npmtoolmixin import NpmToolMixIn


class webpackTool(NpmToolMixIn, BuildTool):
    """webpack is a module bundler (JS world)

Home: https://webpack.js.org
"""
    __slots__ = ()

    def autoDetectFiles(self):
        return 'webpack.config.js'

    def _installTool(self, env):
        try:
            self._name = 'webpack-cli'
            super(webpackTool, self)._installTool(env)
            self._name = 'webpack'
            super(webpackTool, self)._installTool(env)
        finally:
            self._name = 'webpack'

    def _updateTool(self, env):
        try:
            self._name = 'webpack-cli'
            super(webpackTool, self)._updateTool(env)
            self._name = 'webpack'
            super(webpackTool, self)._updateTool(env)
        finally:
            self._name = 'webpack'

    def uninstallTool(self, env):
        try:
            self._name = 'webpack-cli'
            super(webpackTool, self).uninstallTool(env)
            self._name = 'webpack'
            super(webpackTool, self).uninstallTool(env)
        finally:
            self._name = 'webpack'

    def initEnv(self, env, bin_name=None):
        super(webpackTool, self).initEnv(env, bin_name)

        if self._have_tool:
            cli_path = '{0}-cli'.format(env['webpackBin'])
            self._have_tool = self._ospath.exists(cli_path)

            if self._have_tool:
                env['webpackCliBin'] = cli_path

    def onBuild(self, config):
        webpackBin = config['env']['webpackCliBin']
        cmd = [webpackBin, '-p', '--profile', '--display', '--verbose']
        self._executil.callMeaningful(cmd)
