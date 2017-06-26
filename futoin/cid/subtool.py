
from __future__ import print_function, absolute_import

import os

from .mixins.util import UtilMixIn
from .mixins.path import PathMixIn
from .mixins.package import PackageMixIn
from .mixins.version import VersionMixIn

__all__ = ['SubTool']


class SubTool(PathMixIn, PackageMixIn, UtilMixIn, VersionMixIn, object):
    def __init__(self, name):
        self._name = name
        self._have_tool = False

    def getDeps(self):
        return []

    def envDeps(self, env):
        pass

    def getPostDeps(self):
        return []

    def getOrder(self):
        return 0

    def _installTool(self, env):
        self._errorExit(
            'Tool "{0}" must be manually installed'.format(self._name))

    def envNames(self):
        return [self._name + 'Bin']

    def importEnv(self, env):
        environ = os.environ

        for name in self.envNames():
            val = environ.get(name, None)
            if val is not None:
                env[name] = val

    def exportEnv(self, env, dst):
        for name in self.envNames():
            if name in env:
                dst[name] = env[name]

    def initEnv(self, env, bin_name=None):
        name = self._name
        bin_env = name + 'Bin'

        if not env.get(bin_env, None):
            if bin_name is None:
                bin_name = name

            tool_path = self._which(bin_name)
            if tool_path:
                env[bin_env] = tool_path.strip()
                self._have_tool = True
        else:
            self._have_tool = True

    def autoDetect(self, config):
        files = self.autoDetectFiles()

        if files:
            return self._autoDetectByCfg(config, files)

        return False

    def requireInstalled(self, env):
        self.importEnv(env)
        self.initEnv(env)

        if not self._have_tool:
            if self._isExternalToolsSetup(env):
                self._errorExit(
                    'Tool "{0}" must be installed externally (env config)'.format(self._name))
            else:
                self._warn(
                    'Auto-installing required "{0}" tool'.format(self._name))
                self._installTool(env)

            self.initEnv(env)

            if not self._have_tool:
                self._errorExit('Failed to install "{0}"'.format(self._name))

    def isInstalled(self, env):
        self.initEnv(env)
        return self._have_tool

    def updateTool(self, env):
        self.requireInstalled(env)

    def uninstallTool(self, env):
        self._have_tool = False
        self._errorExit(
            'Tool "{0}" must be uninstalled externally'.format(self._name))

    def loadConfig(self, config):
        pass

    def updateProjectConfig(self, config, updates):
        """
updates = {
    name : '...',
    version : '...',
}
@return a list of files to be committed
"""
        return []

    def onExec(self, env, args, replace=True):
        bin = env.get(self._name + 'Bin', None)

        if bin:
            self._callInteractive([bin] + args, replace=replace)
        else:
            self._errorExit(
                'Exec command has not been implemented for "{0}"'.format(self._name))
