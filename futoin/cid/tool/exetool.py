
from ..runtimetool import RuntimeTool


class exeTool(RuntimeTool):
    """Dummy tool to execute files directly"""
    __slots__ = ()

    def initEnv(self, env):
        self._have_tool = True

    def onRun(self, config, svc, args):
        env = config['env']
        self._executil.callInteractive([svc['path']] + args)
