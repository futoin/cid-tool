
import os


class PipToolMixIn(object):
    def getDeps(self):
        return ['pip', 'virtualenv']

    def _pipName(self):
        return self._name

    def _installTool(self, env):
        self._requireBuildDep(env, 'python')

        self._callExternal([env['pipBin'], 'install', '-q', self._pipName()])

    def updateTool(self, env):
        self._callExternal([env['pipBin'], 'install', '-q',
                            '--upgrade', self._pipName()])

    def uninstallTool(self, env):
        self._callExternal([env['pipBin'], 'uninstall',
                            '--yes', '-q', self._pipName()])
        self._have_tool = False

    def initEnv(self, env, bin_name=None):
        name = self._name
        bin_env = name + 'Bin'

        if not env.get(bin_env, None):
            if bin_name is None:
                bin_name = name

            tool_path = os.path.join(env['virtualenvDir'], 'bin', bin_name)

            if os.path.exists(tool_path):
                env[bin_env] = tool_path
                self._have_tool = True
        else:
            self._have_tool = True

    def _requirePythonDev(self, env):
        if int(env['pythonVer'].split('.')[0]) == 3:
            self._requireDeb(['python3-dev'])
            self._requireZypper(['python3-devel'])
            self._requireYumEPEL()
            self._requireYum(['python34-devel'])
            self._requirePacman(['python'])
            self._requireApk('python3-dev')
        else:
            self._requireDeb(['python-dev'])
            self._requireZypper(['python-devel'])
            self._requireYumEPEL()
            self._requireYum(['python-devel'])
            self._requirePacman(['python2'])
            self._requireApk('python2-dev')

        self._requireEmergeDepsOnly(['dev-lang/python'])

    def _requirePip(self, env, package):
        self._callExternal([env['pipBin'], 'install', '-q', package])
