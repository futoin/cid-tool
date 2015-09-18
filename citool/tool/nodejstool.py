
from citool.subtool import SubTool

class nodejsTool( SubTool ):
    def getType( self ):
        return self.TYPE_RUNTIME
    
    def getDeps( self ) :
        return [ 'nvm' ]
