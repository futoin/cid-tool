
from citool.subtool import SubTool
import os

class gitTool( SubTool ):
    def getType( self ):
        return self.TYPE_VCS
    
    def autoDetect( self, config ) :
        return self._autoDetectVCS( config, '.git' )

    def vcsCheckout( self, config, branch ):
        gitBin = config['env']['gitBin']
        wc_dir = config['wcDir']
        
        if os.path.isdir( '.git' ):
            remote_info = self._callExternal( [ gitBin, 'remote', '-v' ] )
            if remote_info.find( config['vcsRepo'] ) < 0 :
                raise RuntimeError( "Git remote mismatch: " + remote_info )
            self._callExternal( [ hgBin, 'fetch' ] )
        elif os.path.exists( wc_dir ):
            raise RuntimeError( "Path already exists: " + wc_dir )
        else :
            self._callExternal( [ gitBin, 'clone', config['vcsRepo'], wc_dir ] )
            os.chdir( wc_dir )

        self._callExternal( [ gitBin, 'checkout', '--track', '-B', branch, 'origin/'+branch ] )
    
    def vcsCommit( self, config, message, files ):
        gitBin = config['env']['gitBin']
        self._callExternal( [ gitBin, 'commit', '-m', message ] + files )
    
    def vcsTag( self, config, tag, message ):
        gitBin = config['env']['gitBin']
        self._callExternal( [ gitBin, 'tag', '-a', '-m', message, tag ] )
    
    def vcsPush( self, config, refs ):
        gitBin = config['env']['gitBin']
        self._callExternal( [ gitBin, 'push', 'origin' ] + refs )
