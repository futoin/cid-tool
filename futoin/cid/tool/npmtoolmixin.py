
class NpmToolMixIn(object):
    def getDeps(self):
        return ['node', 'npm']

    def _npmName(self):
        return self._name

    def _installTool(self, env):
        cmd = [env['npmBin'], 'install', '-g', self._npmName()]

        if self._isAlpineLinux():
            self._trySudoCall(cmd)
        else:
            self._callExternal(cmd)

    def updateTool(self, env):
        cmd = [env['npmBin'], 'update', '-g', self._npmName()]

        if self._isAlpineLinux():
            self._trySudoCall(cmd)
        else:
            self._callExternal(cmd)

    def uninstallTool(self, env):
        cmd = [env['npmBin'], 'uninstall', '-g', self._npmName()]

        if self._isAlpineLinux():
            self._trySudoCall(cmd)
        else:
            self._callExternal(cmd)

        self._have_tool = False
