
from ..buildtool import BuildTool
from ..runenvtool import RunEnvTool
from .piptoolmixin import PipToolMixIn


class dockercomposeTool(PipToolMixIn, BuildTool, RunEnvTool):
    """Compose is a tool for defining and running multi-container Docker applications.

Home: https://docs.docker.com/compose/

Experimental support.
"""

    def autoDetectFiles(self):
        return ['docker-compose.yml', 'docker-compose.yaml']

    def getDeps(self):
        return ['pip', 'docker']

    def getOrder(self):
        return 20

    def _pipName(self):
        return 'docker-compose'

    def _installTool(self, env):
        self._requirePythonDev(env)
        super(dockercomposeTool, self)._installTool(env)

    def onBuild(self, config):
        self._callExternal([config['env']['dockercomposeBin'], 'build'])

    def onPackage(self, config):
        self._callExternal([config['env']['dockercomposeBin'], 'bundle'])

    def initEnv(self, env):
        super(dockercomposeTool, self).initEnv(env, 'docker-compose')
