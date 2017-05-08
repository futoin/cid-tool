
import os

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

    def autoDetectFiles(self):
        return 'setup.py'

    def uninstallTool(self, env):
        pass

    def initEnv(self, env):
        virtualenv_dir = env['virtualenvDir']
        self._have_tool = os.path.exists(
            os.path.join(virtualenv_dir, 'bin', 'easy_install'))

    def onPrepare(self, config):
        targets = self._getTune(config, 'prepare', ['build', 'dist'])

        if not isinstance(targets, list):
            targets = [targets]

        for d in targets:
            if os.path.exists(d):
                self._rmTree(d)

    def onBuild(self, config):
        env = config['env']
        self._requirePip(env, 'wheel')

        targets = self._getTune(config, 'build', ['sdist', 'bdist_wheel'])

        if not isinstance(targets, list):
            targets = [targets]

        self._callExternal([env['pythonBin'], 'setup.py'] + targets)

    def onPackage(self, config):
        target = self._getTune(config, 'package', 'dist')
        self._addPackageFiles(config, os.path.join(target, '*'))

    def onCheck(self, config):
        env = config['env']
        self._requirePip(env, 'docutils')
        self._requirePip(env, 'readme')
        self._callExternal([env['pythonBin'], 'setup.py', 'check', '-mrs'])
