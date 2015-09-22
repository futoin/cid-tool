
from citool.subtool import SubTool
import os

class gitTool( SubTool ):
    def getType( self ):
        return self.TYPE_VCS
    
    def autoDetect( self, config ) :
        return self._autoDetectVCS( config, '.git' )

    def vcsCheckout( self, config, vcs_ref ):
        gitBin = config['env']['gitBin']
        wc_dir = config['wcDir']
        
        if os.path.isdir( wc_dir + '/.git' ):
            os.chdir( wc_dir )
        
        if os.path.isdir( '.git' ):
            if 'vcsRepo' in config:
                remote_info = self._callExternal( [ gitBin, 'remote', '-v' ] )
                if remote_info.find( config['vcsRepo'] ) < 0 :
                    raise RuntimeError( "Git remote mismatch: " + remote_info )

            self._callExternal( [ gitBin, 'fetch', '-q'  ] )
        elif os.path.exists( wc_dir ):
            raise RuntimeError( "Path already exists: " + wc_dir )
        else :
            self._callExternal( [ gitBin, 'clone', '-q', config['vcsRepo'], wc_dir ] )
            os.chdir( wc_dir )

        if  self._callExternal( [ gitBin, 'branch', '-q', '--list', 'origin/'+vcs_ref ] ):
            self._callExternal( [ gitBin, 'checkout', '-q', '--track', '-B', vcs_ref, 'origin/'+vcs_ref ] )
        else :
            self._callExternal( [ gitBin, 'checkout', '-q', vcs_ref ] )
    
    def vcsCommit( self, config, message, files ):
        gitBin = config['env']['gitBin']
        self._callExternal( [ gitBin, 'commit', '-q', '-m', message ] + files )
    
    def vcsTag( self, config, tag, message ):
        gitBin = config['env']['gitBin']
        self._callExternal( [ gitBin, 'tag', '-a', '-m', message, tag ] )
    
    def vcsPush( self, config, refs ):
        gitBin = config['env']['gitBin']
        self._callExternal( [ gitBin, 'push', '-q', 'origin' ] + refs )