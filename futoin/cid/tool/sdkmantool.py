
import os
import subprocess

from ..runenvtool import RunEnvTool
from .bashtoolmixin import BashToolMixIn
from .curltoolmixin import CurlToolMixIn


class sdkmanTool(BashToolMixIn, CurlToolMixIn, RunEnvTool):
    """SDK Man for Java.

Home: http://sdkman.io/
"""
    SDKMAN_DIR_DEFAULT = os.path.join(os.environ['HOME'], '.sdkman')

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

        os.environ['SDKMAN_DIR'] = dir
        self._callBash(env, input=installer)
        del os.environ['SDKMAN_DIR']

    def updateTool(self, env):
        self._callBash(env,
                       'source {0} && sdk selfupgrade'.format(
                           env['sdkmanInit'])
                       )

    def uninstallTool(self, env):
        dir = env['sdkmanDir']

        if os.path.exists(dir):
            self._rmTree(dir)

        self._have_tool = False

    def initEnv(self, env):
        dir = env.setdefault('sdkmanDir', self.SDKMAN_DIR_DEFAULT)
        env_init = os.path.join(dir, 'bin', 'sdkman-init.sh')
        env['sdkmanInit'] = env_init
        self._have_tool = os.path.exists(env_init)

    def onExec(self, env, args, replace=True):
        cmd = '. {0} && sdk {1}'.format(
            env['sdkmanInit'], subprocess.list2cmdline(args))
        self._callBashInteractive(env, cmd, replace=replace)
