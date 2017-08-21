
from ..subtool import SubTool


class NpmToolMixIn(SubTool):
    __slots__ = ()

    def getDeps(self):
        return ['node', 'npm']

    def _npmName(self):
        return self._name

    def _isGlobalNpm(self):
        return self._detect.isAlpineLinux()

    def _installTool(self, env):
        cmd = [env['npmBin'], 'install', '-g', self._npmName()]

        if self._isGlobalNpm():
            self._executil.trySudoCall(cmd + ['--unsafe-perm'])
        else:
            self._executil.callExternal(cmd)

    def updateTool(self, env):
        cmd = [env['npmBin'], 'update', '-g', self._npmName()]

        if self._isGlobalNpm():
            self._executil.trySudoCall(cmd + ['--unsafe-perm'])
        else:
            self._executil.callExternal(cmd)

    def uninstallTool(self, env):
        cmd = [env['npmBin'], 'uninstall', '-g', self._npmName()]

        if self._isGlobalNpm():
            self._executil.trySudoCall(cmd + ['--unsafe-perm'])
        else:
            self._executil.callExternal(cmd)

        self._have_tool = False

    def initEnv(self, env, bin_name=None):
        name = self._name
        bin_env = name + 'Bin'

        if not env.get(bin_env, None):
            if bin_name is None:
                bin_name = name

            npmBinDir = env.get('npmBinDir', None)

            if npmBinDir:
                tool_path = self._ospath.join(npmBinDir, bin_name)

                if self._ospath.exists(tool_path):
                    env[bin_env] = tool_path
                    self._have_tool = True
        else:
            self._have_tool = True
