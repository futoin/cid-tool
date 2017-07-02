
from ..subtool import SubTool


class GemToolMixIn(SubTool):
    __slots__ = ()

    def getDeps(self):
        return ['gem', 'ruby']

    def _gemName(self):
        return self._name

    def _installTool(self, env):
        self._builddep.require(env, 'ruby')

        ver = env.get(self._name + 'Ver', None)
        version_arg = []

        if ver:
            version_arg = ['--version', ver]

        self._executil.callExternal([env['gemBin'], 'install', self._gemName(
        )] + env['gemInstallArgs'].split(' ') + version_arg)

    def updateTool(self, env):
        if env.get(self._name + 'Ver', None):
            self._installTool(env)
        else:
            self._executil.callExternal(
                [env['gemBin'], 'update', self._gemName()] + env['gemInstallArgs'].split(' '))

    def uninstallTool(self, env):
        self._executil.callExternal([env['gemBin'], 'uninstall',
                                     '--force', self._gemName()])
        self._have_tool = False
