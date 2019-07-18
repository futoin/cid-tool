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
from ..testtool import TestTool
from .piptoolmixin import PipToolMixIn


class setuptoolsTool(PipToolMixIn, BuildTool, TestTool):
    """Easily download, build, install, upgrade, and uninstall Python packages.

Home: https://pypi.python.org/pypi/setuptools

Not assumed to be used directly.

Build targets:
    prepare -> {removes build & dist folders}
    build -> ['sdist', 'bdist_wheel']
    package -> {uses result of build in dist/}
Override targets with .config.toolTune.    

"""
    __slots__ = ()

    def autoDetectFiles(self):
        return 'setup.py'

    def uninstallTool(self, env):
        pass

    def initEnv(self, env):
        ospath = self._ospath
        virtualenv_dir = env['virtualenvDir']
        self._have_tool = ospath.exists(
            ospath.join(virtualenv_dir, 'bin', 'easy_install'))

    def onPrepare(self, config):
        targets = self._getTune(config, 'prepare', ['build', 'dist'])
        targets = self._configutil.listify(targets)

        for d in targets:
            self._pathutil.rmTree(d)

    def onBuild(self, config):
        env = config['env']
        self._requirePip(env, 'wheel')

        targets = self._getTune(config, 'build', ['sdist', 'bdist_wheel'])
        targets = self._configutil.listify(targets)

        cmd = [env['pythonBin'], 'setup.py'] + targets
        self._executil.callMeaningful(cmd)

    def onPackage(self, config):
        target = self._getTune(config, 'package', 'dist')
        self._pathutil.addPackageFiles(
            config, self._pathutil.safeJoin(target, '*'))

    def onCheck(self, config):
        env = config['env']
        self._requirePip(env, 'docutils')
        self._requirePip(env, 'readme')
        cmd = [env['pythonBin'], 'setup.py', 'check', '-mrs']
        self._executil.callMeaningful(cmd)
