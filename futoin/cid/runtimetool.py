
from .subtool import SubTool

__all__ = ['RuntimeTool']

class RuntimeTool( SubTool ):
    def onRun( self, config, file, args, tune ):
        env = config['env']
        self._callInteractive([
            env[self._name + 'Bin'], file
        ] + args)
