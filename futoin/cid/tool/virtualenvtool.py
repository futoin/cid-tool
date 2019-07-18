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


class virtualenvTool(BashToolMixIn, RunEnvTool):
    """Virtual Python Environment builder.

Home: https://pypi.python.org/pypi/virtualenv
"""
    __slots__ = ()

    def getDeps(self):
        return ['bash', 'python']

    def getPostDeps(self):
        # we need to ensure that if cid is called from virtualenv env
        # it's still can be used
        # So, CID can be in system and in each virtualenv as well
        return ['cid']

    def envNames(self):
        return ['virtualenvDir', 'virtualenvVer']

    def _installTool(self, env):
        python_ver = env['pythonVer'].split('.')

        virtualenv_dir = env['virtualenvDir']

        # virtualenv depends on ensurepip and provides no setuptools
        # ensurepip is not packaged on all OSes...
        if False:  # and int(python_ver[0]) == 3 and int(python_ver[1]) >= 3:
            self._executil.callExternal([
                env['pythonRawBin'],
                '-m', 'venv',
                '--system-site-packages',
                '--symlinks',
                '--without-pip',  # avoid ensurepip run
                '--clear',
                virtualenv_dir
            ])
        else:
            # Looks quite stupid, but it's a workaround for different OSes
            pip = self._pathutil.which('pip')

            if not pip:
                self._install.debrpm(['python-virtualenv'])
                self._install.debrpm(['virtualenv'])
                self._install.emerge(['dev-python/virtualenv'])
                self._install.pacman(['python-virtualenv'])
                self._install.apk(['py-virtualenv'])

                self._install.deb(['python-pip'])
                self._install.yum(['python2-pip'])
                self._install.emerge(['dev-python/pip'])
                self._install.pacman(['python-pip'])
                self._install.apk('py2-pip')

                if self._detect.isMacOS():
                    self._executil.trySudoCall(['easy_install', 'pip'])

                pip = self._pathutil.which('pip')

            if pip:
                pip_cmd = [pip, 'install', '-q', '--upgrade',
                           'virtualenv>={0}'.format(env['virtualenvVer'])]

                # TODO: use  --user without sudo
                self._executil.trySudoCall(pip_cmd)

            self._setupVirtualenv(env)

    def _setupVirtualenv(self, env):
        virtualenv = self._pathutil.which('virtualenv')

        if not virtualenv:
            self._errorExit('Failed to find virtualenv')

        self._executil.callExternal([
            virtualenv,
            '--python={0}'.format(env['pythonRawBin']),
            '--clear',
            env['virtualenvDir']
        ])

    def _afterExternalSetup(self, env):
        self._setupVirtualenv(env)

    def _updateTool(self, env):
        pass

    def initEnv(self, env):
        ospath = self._ospath
        virtualenv_dir = '.virtualenv-{0}'.format(env['pythonFactVer'])
        virtualenv_dir = env.setdefault(
            'virtualenvDir', ospath.join(self._pathutil.deployHome(), virtualenv_dir))

        env.setdefault('virtualenvVer', '15.1.0')

        self._have_tool = ospath.exists(
            ospath.join(virtualenv_dir, 'bin', 'activate'))

        if self._have_tool:
            env_to_set = self._callBash(env,
                                        'source {0}/bin/activate && env | grep \'{0}\''.format(
                                            virtualenv_dir),
                                        verbose=False
                                        )

            self._pathutil.updateEnvFromOutput(env_to_set)
            # reverse-dep hack
            env['pythonBin'] = ospath.join(virtualenv_dir, 'bin', 'python')
