
from .subtool import SubTool

__all__ = ['RuntimeTool']

class RuntimeTool( SubTool ):
    def getType( self ):
        return self.TYPE_RUNTIME
