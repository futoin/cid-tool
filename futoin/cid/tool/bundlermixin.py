#
# Copyright 2015-2017 (c) Andrey Galkin
#


from ..subtool import SubTool


class BundlerMixIn(SubTool):
    __slots__ = ()

    def getDeps(self):
        return ['bundler']

    def _gemName(self):
        return self._name

    def _installTool(self, env):
        self._have_tool = True
        tcmd = [env['bundlerBin'], 'add', self._gemName()]
        ver = env.get(self._name + 'Ver')

        if ver:
            tcmd.append('--version={0}'.format(ver))

        try:
            self._executil.callExternal(tcmd, verbose=False)
            # self._executil.callMeaningful(tcmd)
        except Exception as e:
            self._warn(str(e))
            bundlerTools = env.setdefault('bundlerTools', {})
            bundlerTools[self._name] = ver
            return

        cmd = [env['bundlerBin'], 'install']
        self._executil.callExternal(cmd, verbose=False)
        # self._executil.callMeaningful(cmd)

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
        # New version is installed, if not in project
        # Otherwise, the project is responsible  for updates
        self._ensureInstalled(env)

    def initEnv(self, env):
        ospath = self._ospath

        bin_path = ospath.join(env['bundlePath'], 'bin', self._name)
        env[self._name + 'Bin'] = bin_path

        if not ospath.exists('Gemfile'):
            # Fake to workaround being required outside of project root (e.g. deployment home)
            self._have_tool = True
            return

        self._have_tool = self._have_tool or ospath.exists(bin_path)

    def onRun(self, config, svc, args):
        env = config['env']
        self._ensureInstalled(env)
        self._executil.callInteractive([
            env['bundlerBin'], 'exec', self._gemName(), '--', svc['path']
        ] + args)

    def _ensureInstalled(self, env):
        bin_path = env.get(self._name + 'Bin')

        if not bin_path or not self._ospath.exists(bin_path):
            self._have_tool = False
            self.installTool(env)
