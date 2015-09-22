
from citool.subtool import SubTool

class nodeTool( SubTool ):
    def getType( self ):
        return self.TYPE_RUNTIME
    
    def getDeps( self ) :
        return [ 'nvm' ]
