
from .subtool import SubTool

__all__ = ['RunEnvTool']

class RunEnvTool( SubTool ):
    def getType( self ):
        return self.TYPE_RUNENV
