
import os

from ..runenvtool import RunEnvTool
from .bashtoolmixin import BashToolMixIn
from .curltoolmixin import CurlToolMixIn


class rvmTool(BashToolMixIn, CurlToolMixIn, RunEnvTool):
    """Ruby Version Manager.

Home: https://rvm.io/

Stable RVM is used by default.
"""

    RVM_DIR_DEFAULT = os.path.join(os.environ['HOME'], '.rvm')
    RVM_LATEST = 'stable'
    RVM_GPG_KEY = '409B6B1796C275462A1703113804BB82D39DC0E3'
    RVM_GET = 'https://get.rvm.io'

    def getDeps(self):
        return (
            ['gpg', 'tar', 'gzip'] +
            BashToolMixIn.getDeps(self) +
            CurlToolMixIn.getDeps(self))

    def _installTool(self, env):
        rvm_dir = env['rvmDir']
        rvm_get = env.get('rvmGet', self.RVM_GET)
        rvm_gpg_key = env.get('rvmGpgKey', self.RVM_GPG_KEY)

        self._callExternal([
            env['gpgBin'], '--keyserver', env['gpgKeyServer'],
            '--recv-keys', rvm_gpg_key
        ], suppress_fail=True)

        os.environ['rvm_user_install_flag'] = '1'
        os.environ['rvm_auto_dotfiles_flag'] = '0'

        installer = self._callCurl(env, [rvm_get])

        # AlpineLinux - required for uninstall
        self._requireApk('procps')

        self._callBash(
            env,
            bash_args=['--', env['rvmVer'], '--path', rvm_dir],
            input=installer)

    def updateTool(self, env):
        self._callExternal([env['rvmBin'], 'get', env['rvmVer']])

    def uninstallTool(self, env):
        try:
            self._callExternal([env['rvmBin'], 'implode', '--force'])
        except:
            pass

        rvm_dir = env['rvmDir']

        if os.path.exists(rvm_dir):
            self._rmTree(rvm_dir)

        self._have_tool = False

    def envNames(self):
        return ['rvmVer', 'rvmDir', 'rvmBin', 'rvmGet', 'rvmGpgKey']

    def initEnv(self, env):
        for v in ['rvm_path', 'rvm_bin_path', 'rvm_prefix', 'rvm_version']:
            try:
                del os.environ[v]
            except:
                pass

        env.setdefault('rvmVer', self.RVM_LATEST)
        rvm_dir = env.setdefault('rvmDir', self.RVM_DIR_DEFAULT)
        rvm_bin_dir = os.path.join(rvm_dir, 'bin')
        rvm_bin = env['rvmBin'] = os.path.join(rvm_bin_dir, 'rvm')
        env['rvmInit'] = os.path.join(rvm_dir, 'scripts', 'rvm')
        self._have_tool = os.path.exists(rvm_bin)
