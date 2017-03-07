
import os

from ..vcstool import VcsTool
from .bashtoolmixin import BashToolMixIn

class hgTool( BashToolMixIn, VcsTool ):
    def getDeps( self ) :
        return [ 'bash' ]
    
    def _installTool( self, env ):
        self._requirePackages(['mercurial'])
        self._requireEmerge(['dev-vcs/mercurial'])
        self._requirePacman(['mercurial'])
    
    def autoDetect( self, config ) :
        return self._autoDetectVCS( config, '.hg' )

    def vcsGetRepo( self, config, wc_dir=None ):
        return self._callExternal( [
            config['env']['hgBin'], '--repository', wc_dir or config['wcDir'], 'paths', 'default'
        ] ).strip()
        
    def vcsCheckout( self, config, vcs_ref ):
        hgBin = config['env']['hgBin']
        wc_dir = config['wcDir']

        if os.path.isdir( '.hg' ):
            if 'vcsRepo' in config:
                remote_info = self.vcsGetRepo( config, '.' )
                if remote_info != config['vcsRepo'] :
                    raise RuntimeError( "Hg remote mismatch: " + remote_info )

            self._callExternal( [ hgBin, 'pull' ] )
        else :
            self._callExternal( [ hgBin, 'clone', config['vcsRepo'], wc_dir ] )

        self._callExternal( [ hgBin, 'checkout', '--check', vcs_ref ] )
    
    def vcsCommit( self, config, message, files ):
        hgBin = config['env']['hgBin']
        self._callExternal( [ hgBin, 'commit', '-m', message ] + files )
    
    def vcsTag( self, config, tag, message ):
        hgBin = config['env']['hgBin']
        self._callExternal( [ hgBin, 'tag', '-m', message, tag ] )
    
    def vcsPush( self, config, refs ):
        env = config['env']
        hgBin = env['hgBin']
        opts = []
        for r in refs :
            is_tag = self._callBash( env,
                '{0} tags | egrep "^{1}" || true'.format( hgBin, r )
            )
            
            if is_tag : continue
                
            opts.append( '-b' )
            opts.append( r )
        self._callExternal( [ hgBin, 'push' ] + opts )
        
    def vcsGetRevision( self, config ) :
        hgBin = config['env']['hgBin']
        return self._callExternal( [ hgBin, 'identify', '--id' ] ).strip()
    
    def _hgCache( self, config, vcs_cache_dir ):
        hgBin = config['env']['hgBin']

        if os.path.isdir( vcs_cache_dir ):
            remote_info = self.vcsGetRepo( config, vcs_cache_dir )

            if remote_info != config['vcsRepo'] :
                self._rmTree( vcs_cache_dir )
            else :
                self._callExternal( [ hgBin, '--cwd', vcs_cache_dir, 'pull' ] )

        if not os.path.isdir( vcs_cache_dir ):
            self._callExternal( [ hgBin, 'clone', config['vcsRepo'], vcs_cache_dir ] )

        
    def vcsGetRefRevision( self, config, vcs_cache_dir, branch ) :
        self._hgCache( config, vcs_cache_dir )
        hgBin = config['env']['hgBin']
        res = self._callExternal( [ hgBin, '--repository', vcs_cache_dir, 'branches' ] ).strip().split("\n")
        for r in res:
            r = r.split()
            
            if r[0] == branch:
                return r[1]
            
        raise RuntimeError( "Uknown Hg ref: {0}".format( branch ) )

    def vcsListTags( self, config, vcs_cache_dir, tag_hint ) :
        self._hgCache( config, vcs_cache_dir )
        hgBin = config['env']['hgBin']
        res = self._callExternal( [ hgBin, '--repository', vcs_cache_dir, 'tags' ] ).strip().split("\n")
        res = [ v.split()[0] for v in res ]
        del res[res.index('tip')]
        return res

    def vcsExport( self, config, vcs_cache_dir, vcs_ref, dst_path ) :
        self._callExternal([
            config['env']['hgBin'],
            '--repository', vcs_cache_dir,
            'archive',
            '--rev', vcs_ref,
            '--type', 'files',
            dst_path
        ])

