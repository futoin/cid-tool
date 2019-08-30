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
from .gemtoolmixin import GemToolMixIn


class bundlerTool(GemToolMixIn, BuildTool):
    """Bundler: The best way to manage a Ruby application's gems.

Home: http://bundler.io/

Note:
1. It will use per-project BUNDLE_PATH=vendor/bundle by default
2. In deployment with missing vendor/bundle, it uses per-deployment BUNDLE_PATH
3. If run outside of project/deployment, standard ~/.bundle is used
"""
    __slots__ = ()

    def envNames(self):
        return ['bundlePath', 'bundlerVer']

    def autoDetectFiles(self):
        return 'Gemfile'

    def initEnv(self, env):
        ospath = self._ospath

        if ospath.exists('vendor/bundle'):
            # packed deps
            bundlePath = self._ospath.realpath('vendor/bundle')
        elif ospath.exists('current/vendor/bundle'):
            # packed deps
            bundlePath = self._ospath.realpath('current/vendor/bundle')
        elif not ospath.exists('Gemfile'):
            # global / deployment
            bundlePath = ospath.join(self._pathutil.deployHome(), '.bundle')
        else:
            # per project
            bundlePath = self._ospath.realpath('vendor/bundle')

        bundlePath = env.setdefault('bundlePath', bundlePath)
        self._environ['BUNDLE_PATH'] = bundlePath

        super(bundlerTool, self).initEnv(env, 'bundle')

    def onPrepare(self, config):
        env = config['env']

        # Dirty hack
        # ---
        bundlerTools = env.get('bundlerTools', {})
        do_bundler_hack = len(bundlerTools) > 0

        for (k, v) in bundlerTools.items():
            tcmd = [env['bundlerBin'], 'add', k]

            if v:
                tcmd.append('--version={0}'.format(v))

            try:
                self._executil.callExternal(tcmd, suppress_fail=True)
            except Exception as e:
                self._warn(str(e))

        if len(bundlerTools) > 0:
            cmd = [env['bundlerBin'], 'install']
            self._executil.callExternal(cmd)

        # Main install
        # ---
        cmd = [env['bundlerBin'], 'install']

        if self._ospath.exists('Gemfile.lock'):
            cmd.append('--deployment')

        self._executil.callMeaningful(cmd)

    def onPackage(self, config):
        if not self._isDefaultPackage(config):
            return

        cmd = [config['env']['bundlerBin'], 'install',
               '--deployment', '--clean']
        self._executil.callMeaningful(cmd)
