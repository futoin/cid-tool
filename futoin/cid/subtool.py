#
# Copyright 2015-2019 Andrey Galkin <andrey@futoin.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from .mixins.ondemand import OnDemandMixIn
from .mixins.log import LogMixIn

__all__ = ['SubTool']


class SubTool(LogMixIn, OnDemandMixIn):
    __slots__ = (
        '_name',
        '_have_tool',
    )

    # TODO: get rid of
    SYSTEM_VER = 'system'

    def __init__(self, name):
        super(SubTool, self).__init__()
        self._name = name
        self._have_tool = False

    def getDeps(self):
        return []

    def getVersionParts(self):
        """Override, if tool has different number of meaningful parts"""
        return 2

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
        environ = self._environ

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

            tool_path = self._pathutil.which(bin_name)
            if tool_path:
                env[bin_env] = tool_path.strip()
                self._have_tool = True
        else:
            self._have_tool = True

    def autoDetect(self, config):
        files = self.autoDetectFiles()

        if files:
            return self._detect.autoDetectByCfg(self._name, config, files)

        return False

    def autoDetectFiles(self):
        return []

    def requireInstalled(self, env):
        self.importEnv(env)
        self.initEnv(env)
        self.installTool(env)

    def installTool(self, env):
        if not self._have_tool:
            if self._detect.isDisabledToolsSetup(env):
                self._errorExit(
                    'Tool "{0}" must be installed externally (env config)'.format(self._name))
            else:
                self._warn(
                    'Auto-installing required "{0}" tool'.format(self._name))

                if self._detect.isExternalToolsSetup(env):
                    self._executil.externalSetup(env, [
                        'tool', 'install',
                        self._name,
                        env.get(self._name + 'Ver', '')])
                    self._afterExternalSetup(env)
                else:
                    self._installTool(env)

            self.initEnv(env)

            if not self._have_tool:
                self._errorExit('Failed to install "{0}"'.format(self._name))

    def _afterExternalSetup(self, env):
        pass

    def isInstalled(self, env):
        self.initEnv(env)
        return self._have_tool

    def updateTool(self, env):
        if self._detect.isDisabledToolsSetup(env):
            self._errorExit(
                'Tool "{0}" must be updated externally (env config)'.format(self._name))
        elif self._detect.isExternalToolsSetup(env):
            self._executil.externalSetup(env, [
                'tool', 'update',
                self._name,
                env.get(self._name + 'Ver', '')])
        else:
            self._updateTool(env)

    def _updateTool(self, env):
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
            self._executil.callInteractive([bin] + args, replace=replace)
        else:
            self._errorExit(
                'Exec command has not been implemented for "{0}"'.format(self._name))

    def _getTune(self, config, key, default=None):
        return config.get('toolTune', {}).get(self._name, {}).get(key, default)

    def sanitizeVersion(self, env):
        """Should be called implicitly by standard CID functionality"""
        ver_var = self._name + 'Ver'
        ver = env.get(ver_var, None)

        if ver:
            end = self.getVersionParts()
            new_ver = ver.split('.')[:end]
            new_ver = '.'.join(new_ver)

            if env[ver_var] != new_ver:
                self._warn('Too precise version "{0}" for "{1}" - trimmed to "{2}"'
                           .format(ver, self._name, new_ver))
                env[ver_var] = new_ver

    def onConfigReset(self):
        self._have_tool = False
