
import os

from .subtool import SubTool

__all__ = ['VcsTool']

class VcsTool( SubTool ):
    def vcsGetRepo( self, config ):
        raise NotImplementedError( self._name )
    
    def vcsCheckout( self, config, branch ):
        raise NotImplementedError( self._name )
    
    def vcsCommit( self, config, message, files ):
        raise NotImplementedError( self._name )
    
    def vcsTag( self, config, tag, message ):
        raise NotImplementedError( self._name )
    
    def vcsPush( self, config, refs ):
        raise NotImplementedError( self._name )
    
    def vcsGetRevision( self, config ) :
        raise NotImplementedError( self._name )
    
    def vcsGetRefRevision( self, config, vcs_cache_dir, branch ) :
        raise NotImplementedError( self._name )

    def vcsListTags( self, config, vcs_cache_dir, tag_hint ) :
        raise NotImplementedError( self._name )

    def vcsExport( self, config, vcs_cache_dir, vcs_ref, dst_path ) :
        raise NotImplementedError( self._name )

    def _autoDetectVCS( self, config, vcsDir ) :
        if config.get( 'vcs', None ) == self._name :
            return True
        
        if os.path.isdir( vcsDir ) :
            if config.get( 'vcs', None ) is not None:
                raise RuntimeError( 'Another VCS type has been already detected!' )
            config['vcs'] = self._name
            return True
        
        return False
