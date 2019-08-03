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


class phoenixTool(RuntimeTool, BuildTool):
    """
    Phoenix - a productive web framework that does not compromise speed or maintainability.

Home: https://phoenixframework.org/

Notes on tuning:
* .tune.prepare
* .tune.build

Note: MIX_ENV is set based on mixEnv or .env.type

It is expected that the server is installed as dependency in the project.
"""

    __slots__ = ()

    def getDeps(self):
        return ['mix']

    def _installTool(self, env):
        pass

    def initEnv(self, env):
        self._have_tool = True

        try:
            self._executil.callExternal(
                [env['mixBin'], 'help', 'phx'], verbose=False)
        except:
            self._info(
                'Tool "{0}" must be installed as project dependency'.format(self._name))

    def onPrepare(self, config):
        target = self._getTune(
            config, 'prepare', ['phx.digest.clean'])
        cmd = [config['env']['mixBin']] + target
        self._executil.callMeaningful(cmd)

    def onBuild(self, config):
        target = self._getTune(
            config, 'build', ['phx.digest'])
        cmd = [config['env']['mixBin']] + target
        self._executil.callMeaningful(cmd)

    def tuneDefaults(self, env):
        return {
            'internal': True,
            'minMemory': '128M',
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
            '--no-compile',
        ]

        # ---

        cmd = [
            config['env']['mixBin'],
            'phx.server',
        ] + mix_args + args

        self._executil.callInteractive(cmd)
