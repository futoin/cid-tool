
from citool.subtool import SubTool
import os

class hgTool( SubTool ):
    def getType( self ):
        return self.TYPE_VCS
    
    def autoDetect( self, config ) :
        return self._autoDetectVCS( config, '.hg' )

    def vcsCheckout( self, config, branch ):
        hgBin = config['env']['hgBin']
        wc_dir = config['wcDir']
        
        if os.path.isdir( '.hg' ):
            remote_info = self._callExternal( [ hgBin, 'paths', branch ] ).strip()
            if remote_info.find( config['vcsRepo'] ) < 0 :
                raise RuntimeError( "Hg remote mismatch: " + remote_info )
            self._callExternal( [ hgBin, 'pull' ] )
        elif os.path.exists( wc_dir ):
            raise RuntimeError( "Path already exists: " + wc_dir )
        else :
            self._callExternal( [ hgBin, 'clone', config['vcsRepo'], wc_dir ] )
            os.chdir( wc_dir )

        self._callExternal( [ hgBin, 'checkout', '--check', branch ] )
    
    def vcsCommit( self, config, message, files ):
        hgBin = config['env']['hgBin']
        self._callExternal( [ hgBin, 'commit', '-m', message ] + files )
    
    def vcsTag( self, config, tag, message ):
        hgBin = config['env']['hgBin']
        self._callExternal( [ hgBin, 'tag', '-m', message, tag ] )
    
    def vcsPush( self, config, refs ):
        hgBin = config['env']['hgBin']
        opts = []
        for r in refs :
            is_tag = self._callExternal( [
                'bash', '-c', '%s tags | egrep "^%s" || true' % ( hgBin, r )
            ] )
            
            if is_tag : continue
                
            opts.append( '-b' )
            opts.append( r )
        self._callExternal( [ hgBin, 'push' ] + opts )
