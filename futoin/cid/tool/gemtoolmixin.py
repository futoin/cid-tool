
class GemToolMixIn(object):
    _REQUIRE_PBDEV = False

    def getDeps(self):
        return ['gem', 'ruby']

    def _gemName(self):
        return self._name

    def _installTool(self, env):
        if self._REQUIRE_PBDEV:
            if env['rubyVer'] == self.SYSTEM_VER:
                self._requireDeb(['ruby-dev'])
                self._requireRpm(['ruby-devel'])
                self._requireApk(['ruby-dev'])
            elif self._isSCLSupported():
                devver = env['rubyVer'].replace('.', '')

                if devver == '19':
                    sclname = 'ruby193-ruby-devel'
                elif devver == '20':
                    sclname = 'ruby200-ruby-devel'
                else:
                    sclname = 'rh-ruby{0}-ruby-devel'.format(devver)

                self._requireRpm(sclname)

            self._requireBuildEssential()

        ver = env.get(self._name + 'Ver', None)
        version_arg = []

        if ver:
            version_arg = ['--version', ver]

        self._callExternal([env['gemBin'], 'install', self._gemName(
        )] + env['gemInstallArgs'].split(' ') + version_arg)

    def updateTool(self, env):
        if env.get(self._name + 'Ver', None):
            self._installTool(env)
        else:
            self._callExternal(
                [env['gemBin'], 'update', self._gemName()] + env['gemInstallArgs'].split(' '))

    def uninstallTool(self, env):
        self._callExternal([env['gemBin'], 'uninstall', self._gemName()])
        self._have_tool = False
