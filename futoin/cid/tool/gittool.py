
import os
import subprocess
import tempfile

from ..vcstool import VcsTool
from .bashtoolmixin import BashToolMixIn

class gitTool( BashToolMixIn, VcsTool ):
    """Git distributed version control system.
    
Home: https://git-scm.com/

Git tool forcibly sets user.email and user.name, 
if not set by user.
"""    
    def getDeps(self):
        return ['bash', 'tar']

    def autoDetectFiles( self ) :
        return '.git'
    
    def _installTool( self, env ):
        self._requirePackages(['git'])
        self._requireEmerge(['dev-vcs/git'])
        self._requirePacman(['git'])
        self._requireHomebrew('git')

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
            
    def _getCurrentBranch( self, config ):
        return self._callExternal( [
            config['env']['gitBin'], 'rev-parse', '--abbrev-ref', 'HEAD'
        ] ).strip()

    def vcsGetRepo( self, config, wc_dir=None ):
        git_dir = wc_dir or os.path.join(os.getcwd(), '.git')
        
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
        wc_dir = os.getcwd()
        vcsRepo = config['vcsRepo']
        
        if os.path.isdir( '.git' ):
            remote_url = self.vcsGetRepo( config, '.git')
            
            if not self._gitCompareRepo( vcsRepo, remote_url ) :
                self._errorExit( "Git remote mismatch: '{0}' != '{1}'"
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

        if files:
            self._callExternal( [ gitBin, 'add' ] + files )
        else:
            self._callExternal( [ gitBin, 'add', '-A' ] )
            files = []

        self._callExternal( [ gitBin, 'commit', '-q', '-m', message ] + files )
    
    def vcsTag( self, config, tag, message ):
        gitBin = config['env']['gitBin']
        self._callExternal( [ gitBin, 'tag', '-a', '-m', message, tag ] )
    
    def vcsPush( self, config, refs, repo=None ):
        refs = refs or []
        gitBin = config['env']['gitBin']
        repo = repo or 'origin'
        self._callExternal( [ gitBin, '-c', 'push.default=current', 'push', '-q', repo ] + refs )
        
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
            return res.split()[0]
        
        self._errorExit( "Uknown Git ref: '{0}'".format( branch ) )
    

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
    
    def vcsListBranches( self, config, vcs_cache_dir, branch_hint ) :
        if branch_hint:
            branch_hint = ['refs/heads/{0}'.format(branch_hint)]
        else:
            branch_hint = []
        
        res = self._callExternal( [
            config['env']['gitBin'],
            'ls-remote','--heads', '--refs',
            config['vcsRepo']
        ] + branch_hint ).strip().split("\n")

        return [ v.split()[1].replace('refs/heads/', '') for v in res ]

    def vcsExport( self, config, vcs_cache_dir, vcs_ref, dst_path ) :
        env = config['env']
        gitBin = env['gitBin']
        vcsRepo = config['vcsRepo']

        if vcs_cache_dir is None:
            cache_repo = vcsRepo
        else:
            if os.path.exists(vcs_cache_dir):
                remote_url = self.vcsGetRepo( config, vcs_cache_dir )
                
                if not self._gitCompareRepo(vcsRepo,  remote_url):
                    self._warn('removing git cache on remote URL mismatch: {0} != {1}'
                        .format(remote_url, vcsRepo))
                    self._rmTree(vcs_cache_dir)
            
            if not os.path.exists(vcs_cache_dir):
                self._callExternal( [
                    env['gitBin'],
                    'clone',
                    '--mirror',
                    '--depth=1',
                    '--no-single-branch',
                    vcsRepo,
                    vcs_cache_dir
                ] )
            else:
                self._callExternal( [
                    env['gitBin'],
                    '--git-dir={0}'.format(vcs_cache_dir),
                    'fetch'
                ] )
                
            cache_repo = 'file://' + vcs_cache_dir
            
        if os.path.exists(dst_path):
            self._rmTree(dst_path)

        os.mkdir(dst_path)
        
        self._callBash(env, '{0} archive --remote={1} --format=tar {2} | {3} x -C {4}'
                .format(config['env']['gitBin'], cache_repo, vcs_ref, env['tarBin'], dst_path))

    def vcsBranch( self, config, vcs_ref ):
        env = config['env']
        gitBin = env['gitBin']
        
        self._callExternal( [
            config['env']['gitBin'],
            'checkout', '-b', vcs_ref,
        ] )
        
        self.vcsPush(config, [vcs_ref])

    def vcsMerge( self, config, vcs_ref, cleanup ):
        curr_ref = self._getCurrentBranch( config )
        
        env = config['env']
        gitBin = env['gitBin']
        
        try:
            self._callExternal( [
                config['env']['gitBin'],
                'merge', '--no-ff', 'origin/'+vcs_ref,
            ] )
        except subprocess.CalledProcessError:
            if cleanup:
                self.vcsRevert(config)
            self._errorExit('Merged failed, aborted.')
        
        self.vcsPush(config, [curr_ref])

    def vcsDelete( self, config, vcs_cache_dir, vcs_ref ):
        env = config['env']
        gitBin = env['gitBin']
        
        have_local = (os.path.exists('.git') and
                      self._gitCompareRepo(config['vcsRepo'],  self.vcsGetRepo(config)))
        
        if have_local:
            try:
                self._callExternal( [
                    config['env']['gitBin'],
                    'branch', '-D', vcs_ref,
                ] )
            except subprocess.CalledProcessError as e:
                self._warn(str(e))
                
            self.vcsPush(config, ['--force', '--delete', vcs_ref])
                
            self._callExternal( [
                config['env']['gitBin'],
                'fetch', '--all', '--prune',
            ] )
        else:
            # a dirty hack to avoid error message of not found
            # local git repo
            repo = tempfile.mkdtemp('fakegit', dir='.')
            
            self._callExternal( [
                config['env']['gitBin'],
                'init', repo,
            ] )

            oldcwd = os.getcwd()
            os.chdir(repo)
            self.vcsPush(config, ['--force', '--delete', vcs_ref], config['vcsRepo'])
            os.chdir(oldcwd)

            self._rmTree(repo)

    def vcsRevert( self, config):
        try:
            self._callExternal( [
                config['env']['gitBin'],
                'merge', '--abort',
            ] )
        except subprocess.CalledProcessError:
            pass

        self._callExternal( [
            config['env']['gitBin'],
            'reset', '--hard',
        ] )

