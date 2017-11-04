#
# Copyright 2015-2017 (c) Andrey Galkin
#


from ..subtool import SubTool


class GemToolMixIn(SubTool):
    __slots__ = ()

    def getDeps(self):
        return ['gem', 'ruby']

    def _gemName(self):
        return self._name

    def _installTool(self, env):
        if self._detect.isExternalToolsSetup(env):
            self._executil.externalSetup(env, ['build-dep', 'ruby'])
        else:
            self._builddep.require(env, 'ruby')

        ver = env.get(self._name + 'Ver', None)
        version_arg = []

        if ver:
            version_arg = ['--version', ver]

        self._executil.callExternal([env['gemBin'], 'install', self._gemName(
        )] + env['gemInstallArgs'].split(' ') + version_arg)

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

    def _updateTool(self, env):
        if env.get(self._name + 'Ver', None):
            self._installTool(env)
        else:
            self._executil.callExternal(
                [env['gemBin'], 'update', self._gemName()] + env['gemInstallArgs'].split(' '))

    def updateTool(self, env):
        if self._detect.isDisabledToolsSetup(env):
            self._errorExit(
                'Tool "{0}" must be updated externally (env config)'.format(self._name))
        else:
            self._updateTool(env)

    def uninstallTool(self, env):
        self._executil.callExternal([env['gemBin'], 'uninstall',
                                     '--force', self._gemName()])
        self._have_tool = False
