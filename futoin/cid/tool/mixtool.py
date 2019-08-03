#
# Copyright 2019 Andrey Galkin <andrey@futoin.org>
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
from ..buildtool import BuildTool


class mixTool(RuntimeTool, BuildTool):
    """
    Mix - elixir build tool.

Home: https://elixir-lang.org/

Notes on tuning:
* .tune.prepare
* .tune.build
* .tune.package
* .tune.package

Note: MIX_ENV is set based on mixEnv or .env.type
"""

    __slots__ = ()

    MIX_EXS = 'mix.exs'

    def autoDetectFiles(self):
        return self.MIX_EXS

    def getDeps(self):
        return ['elixir']

    def envNames(self):
        return ['mixEnv']

    def initEnv(self, env):
        mix_env = env.get('mixEnv', '')

        if mix_env:
            pass
        else:
            mix_env = env['type']

        self._environ['MIX_ENV'] = mix_env
        # ---

        super(mixTool, self).initEnv(env, 'mix')

    def onPrepare(self, config):
        prepareHex = self._getTune(
            config, 'prepareHex', True)

        if prepareHex:
            cmd = [config['env']['mixBin'], 'local.hex', '--force']
            self._executil.callMeaningful(cmd)

        prepareRebar = self._getTune(
            config, 'prepareRebar', True)

        if prepareRebar:
            cmd = [config['env']['mixBin'], 'local.rebar', '--force']
            self._executil.callMeaningful(cmd)

        target = self._getTune(
            config, 'prepare', ['do', 'clean,', 'deps.get'])
        cmd = [config['env']['mixBin']] + target
        self._executil.callMeaningful(cmd)

    def onBuild(self, config):
        target = self._getTune(
            config, 'build', ['do', 'deps.compile,', 'compile'])
        cmd = [config['env']['mixBin']] + target
        self._executil.callMeaningful(cmd)

    def onPackage(self, config):
        target = self._getTune(config, 'package', ['release'])
        cmd = [config['env']['mixBin']] + target
        self._executil.callMeaningful(cmd)

    def tuneDefaults(self, env):
        return {
            'internal': True,
            'minMemory': '64M',
            'debugOverhead': '32M',
            'connMemory': '32K',
            'debugConnOverhead': '64K',
            'socketTypes': ['tcp', 'tcp6'],
            'socketType': 'tcp',
            'scalable': False,
            'reloadable': False,
            'multiCore': True,
            'maxRequestSize': '1M',
            'socketProtocol': 'http',
        }

    def onRun(self, config, svc, args):
        svc_tune = svc['tune']

        # ---
        mix_env = {}

        try:
            mix_env['PORT'] = str(svc_tune['socketPort'])
            mix_env['HOST'] = svc_tune['socketAddress']
        except KeyError:
            pass

        self._environ.update(mix_env)

        # ---
        mix_args = [
            '--no-halt',
            '--no-compile',
            '--preload-modules',
        ]

        # ---

        cmd = [
            config['env']['mixBin'],
            'run',
            svc['path']
        ] + mix_args + args

        self._executil.callInteractive(cmd)
