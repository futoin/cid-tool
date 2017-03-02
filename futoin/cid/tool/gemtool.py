
from ..subtool import SubTool

class gemTool( SubTool ):
    def getType( self ):
        return self.TYPE_BUILD
    
    def getDeps( self ) :
        return [ 'ruby' ]
        
    def uninstallTool( self, env ):
        pass