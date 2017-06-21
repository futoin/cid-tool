
import os
import subprocess

from ..runenvtool import RunEnvTool
from .bashtoolmixin import BashToolMixIn
from .curltoolmixin import CurlToolMixIn


class rustupTool(BashToolMixIn, CurlToolMixIn, RunEnvTool):
    """rustup is an installer for the systems programming language Rust.

Home: https://www.rustup.rs/
"""
    DIR_DEFAULT = os.path.join(os.environ['HOME'], '.multirust')
    CARGO_DIR_DEFAULT = os.path.join(os.environ['HOME'], '.cargo')
    INSTALLER_DEFAULT = 'https://sh.rustup.rs'

    def getDeps(self):
        return (
            BashToolMixIn.getDeps(self) +
            CurlToolMixIn.getDeps(self))

    def _installTool(self, env):
        if self._isAlpineLinux():
            self._warn('Unfortunately, rustup does not support musl libc yet')

        installer = self._callCurl(env, [env['rustupInstaller']])

        self._callBash(
            env,
            bash_args=['--', '-y', '--no-modify-path'],
            input=installer)

    def updateTool(self, env):
        self._callExternal([
            env['rustupBin'], 'self', 'update'
        ])

    def uninstallTool(self, env):
        for v in ['rustupDir', 'cargoDir']:
            dir = env[v]

            if os.path.exists(dir):
                self._rmTree(dir)

        self._have_tool = False

    def envNames(self):
        return ['rustupBin', 'rustupDir', 'rustupInstaller']

    def initEnv(self, env):
        dir = os.environ.setdefault('RUSTUP_HOME', self.DIR_DEFAULT)
        cargo_dir = os.environ.setdefault('CARGO_HOME', self.CARGO_DIR_DEFAULT)

        dir = env.setdefault('rustupDir', dir)
        cargo_dir = env.setdefault('cargoDir', cargo_dir)

        os.environ['RUSTUP_HOME'] = dir
        os.environ['CARGO_HOME'] = cargo_dir

        env.setdefault('rustupInstaller', self.INSTALLER_DEFAULT)

        bin_dir = os.path.join(cargo_dir, 'bin')
        self._addBinPath(bin_dir, True)

        if os.path.exists(os.path.join(bin_dir, 'rustup')):
            super(rustupTool, self).initEnv(env)
