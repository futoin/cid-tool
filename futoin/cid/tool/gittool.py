
import os

from ..vcstool import VcsTool

class gitTool( VcsTool ):
    def autoDetect( self, config ) :
        return self._autoDetectVCS( config, '.git' )
    
    def _installTool( self, env ):
        self.requirePackages(['git'])

    def _checkGitConfig( self, env ):
        gitBin = env['gitBin']
        user_email = None
        user_name = None
        
        try:
            user_email = self._callExternal([
                gitBin, 'config', 'user.email',
            ], verbose=False).strip()
        except:
            pass
        
        try:
            user_name = self._callExternal([
                gitBin, 'config', 'user.name',
            ], verbose=False).strip()
        except:
            pass
        
        if not user_email:
            self._callExternal([
                gitBin, 'config', 'user.email',
                env.get('gitUserEmail', 'noreply@futoin.org')
            ])

        if not user_name:
            self._callExternal([
                gitBin, 'config', 'user.name',
                env.get('gitUserName', 'FutoIn CITool')
            ])

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
        env = config['env']
        gitBin = env['gitBin']
        self._checkGitConfig(env)
        self._callExternal( [ gitBin, 'commit', '-q', '-m', message ] + files )
    
    def vcsTag( self, config, tag, message ):
        gitBin = config['env']['gitBin']
        self._callExternal( [ gitBin, 'tag', '-a', '-m', message, tag ] )
    
    def vcsPush( self, config, refs ):
        gitBin = config['env']['gitBin']
        self._callExternal( [ gitBin, 'push', '-q', 'origin' ] + refs )
        
    def vcsGetRevision( self, config ) :
        gitBin = config['env']['gitBin']
        return self._callExternal( [ gitBin, 'rev-parse', 'HEAD' ] ).strip()

