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


class pipTool(BuildTool):
    """The PyPA recommended tool for installing Python packages.

Home: https://pypi.python.org/pypi/pip
"""
    __slots__ = ()

    REQUIREMENTS_FILES = [
        'requirements.txt',
        'requirements.pip',
    ]

    def autoDetectFiles(self):
        return self.REQUIREMENTS_FILES

    def getDeps(self):
        return ['python', 'virtualenv']

    def envNames(self):
        return ['pipBin', 'pipVer']

    def _installTool(self, env):
        ospath = self._ospath

        if ospath.exists(env['pipBin']):
            self._updateTool(env)
        else:
            self._executil.callExternal([
                ospath.join(env['virtualenvDir'], 'bin',
                            'easy_install'), 'pip'
            ])

    def _updateTool(self, env):
        self._executil.callExternal([
            env['pipBin'], 'install', '-q',
            '--upgrade',
            'pip>={0}'.format(env['pipVer']),
        ])

    def installTool(self, env):
        if not self._have_tool:
            self._installTool(env)
            self.initEnv(env)

            if not self._have_tool:
                self._errorExit('Failed to install "{0}"'.format(self._name))

    def uninstallTool(self, env):
        pass

    def initEnv(self, env):
        ospath = self._ospath
        pipBin = ospath.join(env['virtualenvDir'], 'bin', 'pip')
        pipBin = env.setdefault('pipBin', pipBin)
        pipVer = env.setdefault('pipVer', '9.0.3')

        if ospath.exists(pipBin):
            pipFactVer = self._executil.callExternal(
                [pipBin, '--version'], verbose=False)
            pipFactVer = [int(v) for v in pipFactVer.split(' ')[1].split('.')]
            pipNeedVer = [int(v) for v in pipVer.split('.')]

            self._have_tool = pipNeedVer <= pipFactVer

    def onPrepare(self, config):
        for rf in self.REQUIREMENTS_FILES:
            if self._ospath.exists(rf):
                cmd = [config['env']['pipBin'], 'install', '-r', rf]
                self._executil.callMeaningful(cmd)
