
from ..buildtool import BuildTool

class gemTool( BuildTool ):
    def getDeps( self ) :
        return [ 'ruby' ]
        
    def uninstallTool( self, env ):
        pass