
import os

from ..buildtool import BuildTool


class gemTool(BuildTool):
    """RubyGems: Find, install, and publish RubyGems.

Home: https://rubygems.org/

If rubyVer is equal to system then gems are installed in
user's folder gemDir.

gemDir is equal to ~/.gem by default.

gemInstallArgs is forcibly set by tool depending on its version.
"""

    def getDeps(self):
        return ['ruby']

    def uninstallTool(self, env):
        pass

    def envNames(self):
        return ['gemBin', 'gemDir', 'gemInstallArgs']

    def initEnv(self, env):
        installArgs = []

        if env['rubyVer'] == self.SYSTEM_VER or env['rubyBinOnly']:
            gemDir = os.path.join(self._deployHome(), '.gem', env['rubyVer'])
            gemDir = env.setdefault('gemDir', gemDir)
            os.environ['GEM_HOME'] = gemDir

            self._addEnvPath('GEM_PATH', gemDir)
            self._addBinPath(os.path.join(gemDir, 'bin'), True)
            installArgs += ['--no-user-install', '--no-format-executable']

        super(gemTool, self).initEnv(env)

        if self._have_tool:
            version = self._callExternal(
                [env['gemBin'], '--version'], verbose=False).strip()

            if version >= '2':
                installArgs += ['--no-document']
            else:
                installArgs += ['--no-ri', '--no-rdoc']

            env['gemInstallArgs'] = ' '.join(installArgs)
