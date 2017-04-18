
from __future__ import print_function

import os, re, sys, subprocess

from ..vcstool import VcsTool
from ..rmstool import RmsTool

try:
    import xml.dom.minidom as minidom
except ImportError:
    print('WARNING: missing xml.dom.minidom - SVN will not work', file=sys.stderr)

class svnTool( VcsTool, RmsTool ):
    """Apache Subversion: Enterprise-class centralized version control for the masses.
    
Home: https://subversion.apache.org/
"""    
    def _installTool( self, env ):
        self._requirePackages(['subversion'])
        self._requireEmerge(['dev-vcs/subversion'])
        self._requirePacman(['subversion'])
        self._requireHomebrew('subversion')
        
    def autoDetectFiles( self ):
        return '.svn'
    
    def autoDetect( self, config ) :
        return ( VcsTool.autoDetect( self, config ) or
                 RmsTool.autoDetect( self, config ) )
    
    def vcsGetRepo( self, config, wc_dir=None ):
        svn_info = self._callExternal([
            config['env']['svnBin'], 'info', '--xml', wc_dir or os.getcwd()
        ])
        svn_info = minidom.parseString( svn_info )
        svn_info = svn_info.getElementsByTagName('url')
        url = svn_info[0].firstChild.nodeValue
        url = re.sub( '/(trunk|branches|tags).+$', '', url )
        return url
    
    def _detectSVNPath( self, config, vcs_ref ):
        env = config['env']
        svnBin = env['svnBin']
        vcsRepo = config['vcsRepo']        
        branch_path = '{0}/branches/{1}'.format( vcsRepo, vcs_ref )
        tag_path = '{0}/tags/{1}'.format( vcsRepo, vcs_ref )
        
        if vcs_ref == 'trunk':
            svn_repo_path = '{0}/trunk'.format( vcsRepo )
        elif self._callExternal( [ svnBin, 'ls', branch_path ], suppress_fail=True ) :
            svn_repo_path = branch_path
        elif self._callExternal( [ svnBin, 'ls', tag_path ], suppress_fail=True ) :
            svn_repo_path = tag_path
        else:
            self._errorExit( "VCS ref was not found: " + vcs_ref )
            
        return svn_repo_path
    
    def vcsCheckout( self, config, vcs_ref ):
        env = config['env']
        svnBin = env['svnBin']
        wc_dir = os.getcwd()
        
        svn_repo_path = self._detectSVNPath(config, vcs_ref)

        if os.path.isdir( '.svn' ):
            self._callExternal( [ svnBin, 'switch', svn_repo_path ] )
        else:
            self._callExternal(
                [ svnBin, 'checkout',
                 svn_repo_path,
                 wc_dir ] )
    
    def vcsCommit( self, config, message, files ):
        svnBin = config['env']['svnBin']
        if files:
            commit_files = files
        else:
            commit_files = []
            files = ['--depth=infinity', '.']

        self._callExternal( [ svnBin, 'add', '--force', ] + files )

        self._callExternal(
                [ svnBin, 'commit',
                 '-m', message ] + commit_files )
    
    def vcsTag( self, config, tag, message ):
        env = config['env']
        svnBin = env['svnBin']

        svn_info = self._callExternal([
            config['env']['svnBin'], 'info', '--xml'
        ])
        svn_info = minidom.parseString( svn_info )
        svn_info = svn_info.getElementsByTagName('url')
        svn_url = svn_info[0].firstChild.nodeValue

        self._callExternal( [
            svnBin, 'copy',
            '-m', message,
            '--parents',
            svn_url,
            '%s/tags/%s' % ( config['vcsRepo'], tag )
        ] )
    
    def vcsPush( self, config, refs ):
        pass
        
    def vcsGetRevision( self, config ) :
        svnBin = config['env']['svnBin']
        svn_info = self._callExternal( [ svnBin, 'info',  '--xml' ] )
        
        svn_info = minidom.parseString( svn_info )
        svn_info = svn_info.getElementsByTagName('commit')

        if len(svn_info):
            return svn_info[0].getAttribute('revision')
            
        return 'local'

    def vcsGetRefRevision( self, config, vcs_cache_dir, branch ) :
        svnBin = config['env']['svnBin']
        
        svn_repo_path = self._detectSVNPath(config, branch)
            
        res = self._callExternal( [ svnBin, 'info', svn_repo_path, '--xml' ] )
        
        res = minidom.parseString( res )
        return res.getElementsByTagName('commit')[0].getAttribute('revision')

    def vcsListTags( self, config, vcs_cache_dir, tag_hint ) :
        svnBin = config['env']['svnBin']
        vcsRepo = config['vcsRepo']
        svn_repo_path = '{0}/tags/'.format( vcsRepo )
        res = self._callExternal( [ svnBin, 'ls', svn_repo_path ] ).strip().split("\n")
        return [v.replace(svn_repo_path, '').replace('/', '') for v in res ]
    
    def vcsListBranches( self, config, vcs_cache_dir, branch_hint ) :
        svnBin = config['env']['svnBin']
        vcsRepo = config['vcsRepo']
        svn_repo_path = '{0}/branches/'.format( vcsRepo )
        res = self._callExternal( [ svnBin, 'ls', svn_repo_path ] ).strip().split("\n")
        return [v.replace(svn_repo_path, '').replace('/', '') for v in res ]

    def vcsExport( self, config, vcs_cache_dir, vcs_ref, dst_path ) :
        svnBin = config['env']['svnBin']
        
        svn_repo_path = self._detectSVNPath(config, vcs_ref)
        
        if os.path.exists(dst_path):
            os.rmdir(dst_path)
        
        if vcs_cache_dir is None:
            self._callExternal( [ svnBin, 'export', svn_repo_path, dst_path ] )
            return
            
        if os.path.isdir( vcs_cache_dir ):
            cnd = 'switch'
        else:
            cnd = 'checkout'
            
        self._callExternal( [ svnBin, cnd, svn_repo_path, vcs_cache_dir ] )
        self._callExternal( [ svnBin, 'export', vcs_cache_dir, dst_path ] )
    
    def vcsBranch( self, config, vcs_ref ):
        svnBin = config['env']['svnBin']
        vcsRepo = config['vcsRepo']
        svn_repo_path = '{0}/branches/{1}'.format( vcsRepo, vcs_ref )
        self._callExternal( [ svnBin, 'update' ] )
        self._callExternal( [ svnBin, 'copy', '-m', 'CID branch ' + vcs_ref, '.', svn_repo_path ] )
        self.vcsCheckout(config, vcs_ref)

    def vcsMerge( self, config, vcs_ref, cleanup ):
        svnBin = config['env']['svnBin']
        
        svn_repo_path = self._detectSVNPath(config, vcs_ref)

        self._callExternal( [ svnBin, 'update' ] )
        self._callExternal( [ svnBin, 'merge', '--accept', 'postpone', svn_repo_path ] )
        
        try:
            self._callExternal( [ svnBin, 'commit', '-m', 'CID merged ' + vcs_ref ] )
        except subprocess.CalledProcessError:
            if cleanup:
                self.vcsRevert(config)
            self._errorExit('Merged failed, aborted.')

    def vcsDelete( self, config, vcs_cache_dir, vcs_ref ):
        svnBin = config['env']['svnBin']
        vcsRepo = config['vcsRepo']
        svn_repo_path = '{0}/branches/{1}'.format( vcsRepo, vcs_ref )
        self._callExternal( [ svnBin, 'remove', '-m', 'CID delete ' + vcs_ref, svn_repo_path ] )

    def vcsRevert( self, config):
        svnBin = config['env']['svnBin']
        self._callExternal( [ svnBin, 'revert', '-R', '.' ] )

