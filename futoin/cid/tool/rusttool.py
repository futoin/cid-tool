
import os

from ..runenvtool import RunEnvTool


class rustTool(RunEnvTool):
    """Rust is a systems programming language.

Home: https://www.rust-lang.org
"""

    def getDeps(self):
        if self._useSystem():
            return []

        return ['rustup']

    def getVersionParts(self):
        return 3

    def _useSystem(self):
        return self._isAlpineLinux()

    def _installTool(self, env):
        if self._useSystem():
            self._requireApk('rust')
            return

        self._callExternal([
            env['rustupBin'], 'toolchain', 'install', env['rustVer']
        ])

    def updateTool(self, env):
        self._installTool(env)

    def uninstallTool(self, env):
        if self._useSystem():
            return

        self._callExternal([
            env['rustupBin'], 'toolchain', 'uninstall', env['rustVer']
        ])
        self._have_tool = False

    def envNames(self):
        return ['rustBin', 'rustVer']

    def initEnv(self, env):
        if not self._useSystem():
            ver = env.setdefault('rustVer', 'stable')
            os.environ['RUSTUP_TOOLCHAIN'] = ver

            try:
                res = self._callExternal([
                    env['rustupBin'], 'which', 'rustc'
                ], verbose=False)
            except:
                return

        super(rustTool, self).initEnv(env, 'rustc')
