
from ..runtimetool import RuntimeTool

class exeTool( RuntimeTool ):
    """Dummy tool to execute files directly"""
    
    def initEnv(self, env):
        self._have_tool = True
    
    def onRun( self, config, file, args, tune ):
        env = config['env']
        self._callInteractive([file] + args)
