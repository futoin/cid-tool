
from citool.subtool import SubTool

class hgTool( SubTool ):
    def getType( self ):
        return self.TYPE_VCS
    
    def autoDetect( self, config ) :
        return self._autoDetectVCS( config, '.hg' )

    def vcsCheckout( self, config, branch ):
        raise NotImplementedError( self._name )
    
    def vcsCommit( self, config, message, files ):
        raise NotImplementedError( self._name )
    
    def vcsTag( self, config, tag, message ):
        raise NotImplementedError( self._name )
    
    def vcsPush( self, config, refs ):
        raise NotImplementedError( self._name )
