
from .subtool import SubTool

__all__ = ['BuildTool']

class BuildTool( SubTool ):
    def getType( self ):
        return self.TYPE_BUILD
