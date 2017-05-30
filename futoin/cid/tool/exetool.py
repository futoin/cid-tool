
from ..runtimetool import RuntimeTool


class exeTool(RuntimeTool):
    """Dummy tool to execute files directly"""

    def initEnv(self, env):
        self._have_tool = True

    def onRun(self, config, svc, args):
        env = config['env']
        self._callInteractive([svc['path']] + args)
