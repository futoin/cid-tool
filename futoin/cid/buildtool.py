
from .subtool import SubTool

class BuildTool( SubTool ):
    def getType( self ):
        return self.TYPE_BUILD
