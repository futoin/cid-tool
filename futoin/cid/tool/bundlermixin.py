
from ..subtool import SubTool


class BundlerMixIn(SubTool):
    __slots__ = ()

    def getDeps(self):
        return ['bundler']

    def _gemName(self):
        return self._name

    def _installTool(self, env):
        if self._detect.isExternalToolsSetup(env):
            self._executil.externalSetup(env, ['build-dep', 'ruby'])
        else:
            self._builddep.require(env, 'ruby')

        ver = env.get(self._name + 'Ver', None)

        cmd = [env['bundlerBin'], 'add', self._gemName()]

        if ver:
            cmd += ['--version', ver]

        self._executil.callExternal(cmd)

        cmd = [env['bundlerBin'], 'install', '--quiet']
        self._executil.callExternal(cmd)

    def installTool(self, env):
        if not self._have_tool:
            if self._detect.isDisabledToolsSetup(env):
                self._errorExit(
                    'Tool "{0}" must be installed externally (env config)'.format(self._name))
            else:
                self._warn(
                    'Auto-installing required "{0}" tool'.format(self._name))
                self._installTool(env)

            self.initEnv(env)

            if not self._have_tool:
                self._errorExit('Failed to install "{0}"'.format(self._name))

    def updateTool(self, env):
        if self._detect.isDisabledToolsSetup(env):
            self._errorExit(
                'Tool "{0}" must be updated externally (env config)'.format(self._name))
        else:
            self._updateTool(env)

    def initEnv(self, env):
        if not self._ospath.exists('Gemfile'):
            # Fake to workaround being required outside of project root (e.g. deployment home)
            self._have_tool = True
            return

        ospath = self._ospath
        bin_path = ospath.join(env['bundlePath'], 'bin', self._name)
        self._have_tool = ospath.exists(bin_path)
