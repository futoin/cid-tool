
from citool.subtool import SubTool

class rubyTool( SubTool ):
    def getType( self ):
        return self.TYPE_RUNTIME
    
    def getDeps( self ) :
        return [ 'rvm' ]
