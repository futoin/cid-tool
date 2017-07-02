
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
            self._executil.trySudoCall(cmd)
        else:
            self._executil.callExternal(cmd)

    def updateTool(self, env):
        cmd = [env['npmBin'], 'update', '-g', self._npmName()]

        if self._isGlobalNpm():
            self._executil.trySudoCall(cmd)
        else:
            self._executil.callExternal(cmd)

    def uninstallTool(self, env):
        cmd = [env['npmBin'], 'uninstall', '-g', self._npmName()]

        if self._isGlobalNpm():
            self._executil.trySudoCall(cmd)
        else:
            self._executil.callExternal(cmd)

        self._have_tool = False
