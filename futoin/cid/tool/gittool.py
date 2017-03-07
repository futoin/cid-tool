
import os

from ..vcstool import VcsTool
from .bashtoolmixin import BashToolMixIn

class gitTool( BashToolMixIn, VcsTool ):
    _rev = None
    
    def getDeps(self):
        return ['bash', 'tar']

    def autoDetect( self, config ) :
        return self._autoDetectVCS( config, '.git' )
    
    def _installTool( self, env ):
        self._requirePackages(['git'])
        self._requireEmerge(['dev-vcs/git'])
        self._requirePacman(['git'])

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

    def vcsGetRepo( self, config, wc_dir=None ):
        git_dir = wc_dir or os.path.join(config['wcDir'], '.git')
        
        return self._callExternal( [
            config['env']['gitBin'],
            '--git-dir={0}'.format(git_dir),
            'config',
            '--get',
            'remote.origin.url'
        ] ).strip()
    
    def _gitCompareRepo( self, cfg, act ):
        return cfg == act or ('ssh://'+cfg) == act
    
    def vcsCheckout( self, config, vcs_ref ):
        gitBin = config['env']['gitBin']
        wc_dir = config['wcDir']
        vcsRepo = config['vcsRepo']
        
        if os.path.isdir( '.git' ):
            remote_url = self.vcsGetRepo( config, '.git')
            
            if not self._gitCompareRepo( vcsRepo, remote_url ) :
                raise RuntimeError( "Git remote mismatch: {0} != {1}"
                    .format(vcsRepo, remote_url ) )

            self._callExternal( [ gitBin, 'fetch', '-q'  ] )
        else :
            self._callExternal( [ gitBin, 'clone', '-q', vcsRepo, wc_dir ] )
            
        remote_branch = self._callExternal( [ gitBin, 'branch', '-q', '--list', 'origin/'+vcs_ref ] ).strip()
            
        if self._callExternal( [ gitBin, 'branch', '-q', '--list', vcs_ref ] ).strip():
            self._callExternal( [ gitBin, 'checkout', '-q', vcs_ref ] )

            if remote_branch:
                self._callExternal( [ gitBin, 'branch', '-q', '--set-upstream-to', 'origin/'+vcs_ref ] )
                self._callExternal( [ gitBin, 'rebase', 'origin/'+vcs_ref  ] )
        elif remote_branch:
            self._callExternal( [ gitBin, 'checkout', '-q', '--track', '-b', vcs_ref, 'origin/'+vcs_ref ] )
        else:
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
    
    def vcsGetRefRevision( self, config, vcs_cache_dir, branch ) :
        res = self._callExternal( [
            config['env']['gitBin'],
            'ls-remote', '--refs',
            config['vcsRepo'],
            'refs/heads/{0}'.format(branch)
        ] ).strip()
        
        if res:
            self._rev = res.split()[0]
            return self._rev
        
        raise RuntimeError( "Uknown Git ref: {0}".format( branch ) )
    

    def vcsListTags( self, config, vcs_cache_dir, tag_hint ) :
        if tag_hint:
            tag_hint = ['refs/tags/{0}'.format(tag_hint)]
        else:
            tag_hint = []
        
        res = self._callExternal( [
            config['env']['gitBin'],
            'ls-remote','--tags', '--refs',
            config['vcsRepo']
        ] + tag_hint ).strip().split("\n")

        return [ v.split()[1].replace('refs/tags/', '') for v in res ]

    def vcsExport( self, config, vcs_cache_dir, vcs_ref, dst_path ) :
        env = config['env']
        gitBin = env['gitBin']
        vcsRepo = config['vcsRepo']

        if os.path.exists(vcs_cache_dir):
            remote_url = self.vcsGetRepo( config, vcs_cache_dir )
            
            if self._gitCompareRepo(vcsRepo,  remote_url):
                print('WARNING: removing git cache on remote URL mismatch: {0} != {1}'
                      .format(remote_url, vcsRepo))
                self._rmTree(vcs_cache_dir)
        
        if not os.path.exists(vcs_cache_dir):
             self._callExternal( [
                env['gitBin'],
                'clone', '--mirror',
                vcsRepo,
                vcs_cache_dir
            ] )
        else:
            self._callExternal( [
                env['gitBin'],
                '--git-dir={0}'.format(vcs_cache_dir),
                'fetch'
            ] )
            
        if os.path.exists(dst_path):
            self._rmTree(dst_path)

        os.mkdir(dst_path)
        
        if self._rev:
            vcs_ref = self._rev
        
        self._callBash(env, '{0} --git-dir={1} archive --format=tar {2} | {3} x -C {4}'
                .format(config['env']['gitBin'], vcs_cache_dir, vcs_ref, env['tarBin'], dst_path))

