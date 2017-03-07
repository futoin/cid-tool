
import os, re
import xml.dom.minidom

from ..vcstool import VcsTool
from ..rmstool import RmsTool

class svnTool( VcsTool, RmsTool ):
    _rev = None
    
    def _installTool( self, env ):
        self._requirePackages(['subversion'])
        self._requireEmerge(['dev-vcs/subversion'])
        self._requirePacman(['subversion'])
    
    def autoDetect( self, config ) :
        return ( self._autoDetectVCS( config, '.svn' )
                or RmsTool.autoDetect( self, config ) )
    
    def vcsGetRepo( self, config, wc_dir=None ):
        svn_info = self._callExternal([
            config['env']['svnBin'], 'info', '--xml', wc_dir or config['wcDir']
        ])
        svn_info = xml.dom.minidom.parseString( svn_info )
        svn_info = svn_info.getElementsByTagName('url')
        url = svn_info[0].firstChild.nodeValue
        url = re.sub( '/(trunk|branches|tags).+$', '', url )
        return url
    
    def vcsCheckout( self, config, vcs_ref ):
        env = config['env']
        svnBin = env['svnBin']
        wc_dir = config['wcDir']
            
        branch_path = '%s/branches/%s' % ( config['vcsRepo'], vcs_ref )
        tag_path = '%s/tags/%s' % ( config['vcsRepo'], vcs_ref )
        
        if self._callExternal( [ svnBin, 'ls', branch_path ], suppress_fail=True ) :
            svn_repo_path = branch_path
        elif self._callExternal( [ svnBin, 'ls', tag_path ], suppress_fail=True ) :
            svn_repo_path = tag_path
        else:
            raise RuntimeError( "VCS ref was not found: " + vcs_ref )

        if os.path.isdir( '.svn' ):
            self._callExternal( [ svnBin, 'switch', svn_repo_path ] )
        else:
            self._callExternal(
                [ svnBin, 'checkout',
                 svn_repo_path,
                 wc_dir ] )
    
    def vcsCommit( self, config, message, files ):
        svnBin = config['env']['svnBin']
        self._callExternal(
                [ svnBin, 'commit',
                 '-m', message ] + files )
    
    def vcsTag( self, config, tag, message ):
        env = config['env']
        svnBin = env['svnBin']

        svn_info = self._callExternal([
            config['env']['svnBin'], 'info', '--xml'
        ])
        svn_info = xml.dom.minidom.parseString( svn_info )
        svn_info = svn_info.getElementsByTagName('url')
        svn_url = svn_info[0].firstChild.nodeValue

        self._callExternal( [
            svnBin, 'copy',
            '-m', message,
            svn_url,
            '%s/tags/%s' % ( config['vcsRepo'], tag )
        ] )
    
    def vcsPush( self, config, refs ):
        pass
        
    def vcsGetRevision( self, config ) :
        svnBin = config['env']['svnBin']
        svn_info = self._callExternal( [ svnBin, 'info',  '--xml' ] )
        
        svn_info = xml.dom.minidom.parseString( svn_info )
        svn_info = svn_info.getElementsByTagName('commit')

        if len(svn_info):
            return svn_info[0].getAttribute('revision')
            
        return 'local'

    def vcsGetRefRevision( self, config, vcs_cache_dir, branch ) :
        svnBin = config['env']['svnBin']
        
        if branch == 'trunk':
            svn_repo_path = '{0}/{1}'.format( config['vcsRepo'], branch )
        else :
            svn_repo_path = '{0}/branches/{1}'.format( config['vcsRepo'], branch )
            
        res = self._callExternal( [ svnBin, 'info', svn_repo_path, '--xml' ] )
        
        res = xml.dom.minidom.parseString( res )
        self._rev = res.getElementsByTagName('commit')[0].getAttribute('revision')
        return self._rev

    def vcsListTags( self, config, vcs_cache_dir, tag_hint ) :
        svnBin = config['env']['svnBin']
        vcsRepo = config['vcsRepo']
        svn_repo_path = '{0}/tags/'.format( vcsRepo )
        res = self._callExternal( [ svnBin, 'ls', svn_repo_path ] ).strip().split("\n")
        return [v.replace(svn_repo_path, '').replace('/', '') for v in res ]

    def vcsExport( self, config, vcs_cache_dir, vcs_ref, dst_path ) :
        svnBin = config['env']['svnBin']
        
        if self._rev :
            if vcs_ref == 'trunk':
                svn_repo_path = '{0}/{1}@{2}'.format( config['vcsRepo'], vcs_ref, self._rev )
            else :
                svn_repo_path = '{0}/branches/{1}@{2}'.format( config['vcsRepo'], vcs_ref, self._rev )
        else :
            svn_repo_path = '{0}/tags/{1}'.format( config['vcsRepo'], vcs_ref )
        
        if os.path.isdir( vcs_cache_dir ):
            cnd = 'switch'
        else:
            cnd = 'checkout'
            
        self._callExternal( [ svnBin, cnd, svn_repo_path, vcs_cache_dir ] )
        self._callExternal( [ svnBin, 'export', vcs_cache_dir, dst_path ] )


