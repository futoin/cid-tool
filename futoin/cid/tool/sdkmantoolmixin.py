
import os
import re

from .bashtoolmixin import BashToolMixIn
from .javatoolmixin import JavaToolMixIn


class SdkmanToolMixIn(BashToolMixIn, JavaToolMixIn):
    _NEED_JDK = True

    def getDeps(self):
        return (
            super(SdkmanToolMixIn, self).getDeps() +
            ['sdkman', 'java'] +
            (self._NEED_JDK and ['jdk'] or [])
        )

    def _sdkName(self):
        return self._name

    def _binName(self):
        return self._name

    def _setAutoAnswer(self, env):
        self._callBash(env,
                       'grep -q "sdkman_auto_answer=true" {0} || echo "sdkman_auto_answer=true" >> {0}'
                       .format(os.path.join(env['sdkmanDir'], 'etc', 'config')),
                       verbose=False
                       )

    def _callSdkman(self, env, cmd, verbose=True):
        return self._callBash(env,
                              'source {0} >/dev/null && sdk {1}'.format(
                                  env['sdkmanInit'],
                                  cmd
                              ),
                              verbose=verbose
                              )

    def _javaVersion(self, env):
        if not env.get('javaBin', None):
            return 0

        java_ver = self._callBash(
            env, '{0} -version 2>&1'.format(env['javaBin']), verbose=False)
        return int(re.search('version "1\.([0-9]+)\.', java_ver).group(1))

    def _installTool(self, env):
        self._setAutoAnswer(env)
        self._callSdkman(env,
                         'install {0} {1}'.format(
                             self._sdkName(),
                             env.get(self._name + 'Ver', '')
                         )
                         )

    def updateTool(self, env):
        self._setAutoAnswer(env)
        self._callSdkman(env,
                         'upgrade {0}'.format(
                             self._sdkName()
                         )
                         )

    def uninstallTool(self, env):
        tool_dir = os.path.join(
            env['sdkmanDir'], 'candidates', self._sdkName())
        if os.path.exists(tool_dir):
            self._info('Removing: {0}'.format(tool_dir))
            self._rmTree(tool_dir)
        #self._setAutoAnswer( env )
        # self._callSdkman( env,
        #    'uninstall {0} {1}'.format(
        #        self._sdkName(),
        #        env.get(self._name + 'Ver', '')
        #    )
        #)

    def initEnv(self, env):
        if not env.get('sdkmanDir', None):
            return

        tool_dir = os.path.join(
            env['sdkmanDir'], 'candidates', self._sdkName(), 'current')

        if not os.path.exists(tool_dir):
            return

        try:
            env_to_set = self._callSdkman(env,
                                          'use {0} {1} >/dev/null && env | grep -i {0}'
                                          .format(self._sdkName(), env.get(self._name + 'Ver', '')),
                                          verbose=False
                                          )
        except:
            return

        if env_to_set:
            self._updateEnvFromOutput(env_to_set)
            super(SdkmanToolMixIn, self).initEnv(env, self._binName())
