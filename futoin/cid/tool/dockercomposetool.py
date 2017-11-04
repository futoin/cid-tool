#
# Copyright 2015-2017 (c) Andrey Galkin
#


from ..buildtool import BuildTool
from ..runenvtool import RunEnvTool
from .piptoolmixin import PipToolMixIn


class dockercomposeTool(PipToolMixIn, BuildTool, RunEnvTool):
    """Compose is a tool for defining and running multi-container Docker applications.

Home: https://docs.docker.com/compose/

Experimental support.
"""
    __slots__ = ()

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
        cmd = [config['env']['dockercomposeBin'], 'build']
        self._executil.callMeaningful(cmd)

    def onPackage(self, config):
        cmd = [config['env']['dockercomposeBin'], 'bundle']
        self._executil.callMeaningful(cmd)

    def initEnv(self, env):
        super(dockercomposeTool, self).initEnv(env, 'docker-compose')
