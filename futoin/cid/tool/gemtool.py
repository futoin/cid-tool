
from ..buildtool import BuildTool


class gemTool(BuildTool):
    """RubyGems: Find, install, and publish RubyGems.

Home: https://rubygems.org/

If rubyVer is equal to system then gems are installed in
user's folder gemDir.

gemDir is equal to ~/.gem by default.

gemInstallArgs is forcibly set by tool depending on its version.
"""
    __slots__ = ()

    def getDeps(self):
        return ['ruby']

    def uninstallTool(self, env):
        pass

    def envNames(self):
        return ['gemBin', 'gemDir', 'gemInstallArgs']

    def initEnv(self, env):
        ospath = self._ospath
        environ = self._environ
        installArgs = []

        if env['rubyVer'] == self.SYSTEM_VER or env['rubyBinOnly']:
            gemDir = ospath.join(self._pathutil.deployHome(),
                                 '.gem', env['rubyVer'])
            gemDir = env.setdefault('gemDir', gemDir)
            environ['GEM_HOME'] = gemDir
            environ['GEM_PATH'] = gemDir
            environ['GEM_SPEC_CACHE'] = ospath.join(gemDir, 'specs')

            #self._pathutil.addEnvPath('GEM_PATH', gemDir)
            self._pathutil.addBinPath(ospath.join(gemDir, 'bin'), True)
            installArgs += ['--no-user-install', '--no-format-executable']

        super(gemTool, self).initEnv(env)

        if self._have_tool:
            version = self._executil.callExternal(
                [env['gemBin'], '--version'], verbose=False).strip()

            if version >= '2':
                installArgs += ['--no-document']
            else:
                installArgs += ['--no-ri', '--no-rdoc']

            env['gemInstallArgs'] = ' '.join(installArgs)
