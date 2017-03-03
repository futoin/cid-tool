
import os
import re

from ..vcstool import VcsTool

class svnTool( VcsTool ):
    def getDeps( self ) :
        return [ 'bash' ]
    
    def _installTool( self, env ):
        self.requirePackages(['subversion'])
    
    def autoDetect( self, config ) :
        return self._autoDetectVCS( config, '.svn' )
    
    def vcsCheckout( self, config, vcs_ref ):
        env = config['env']
        svnBin = env['svnBin']
        bash_bin = env['bashBin']
        wc_dir = config['wcDir']
            
        if os.path.isdir( wc_dir + '/.svn' ):
            os.chdir( wc_dir )
            
        if 'vcsRepo' not in config:
            svn_info = self._callExternal( [ svnBin, 'info' ] ).split("\n")
            
            for si in svn_info:
                si = si.split( ': ', 1 )
                if si[0] == 'URL':
                    config['vcsRepo'] = re.sub( '/(trunk|branches|tags).+$', '', si[1] )
                    break
            
        branch_path = '%s/branches/%s' % ( config['vcsRepo'], vcs_ref )
        tag_path = '%s/tags/%s' % ( config['vcsRepo'], vcs_ref )
        
        if self._callExternal( [
                bash_bin,  '--noprofile', '--norc', '-c',
                '%s ls %s 2>/dev/null' % ( svnBin, branch_path )
                ], suppress_fail=True ) :
            svn_repo_path = branch_path
        elif self._callExternal( [ svnBin, 'ls', tag_path ] ) :
            svn_repo_path = tag_path
        else:
            raise RuntimeError( "VCS ref was not found: " + vcs_ref )

        if os.path.isdir( '.svn' ):
            self._callExternal( [ svnBin, 'switch', svn_repo_path ] )
        elif os.path.exists( wc_dir ):
            raise RuntimeError( "Path already exists: " + wc_dir )
        else:
            self._callExternal(
                [ svnBin, 'checkout',
                 svn_repo_path,
                 wc_dir ] )
            os.chdir( wc_dir )
    
    def vcsCommit( self, config, message, files ):
        svnBin = config['env']['svnBin']
        self._callExternal(
                [ svnBin, 'commit',
                 '-m', message ] + files )
    
    def vcsTag( self, config, tag, message ):
        env = config['env']
        svnBin = env['svnBin']
        bash_bin = env['bashBin']

        svn_url = self._callExternal( [
            bash_bin,  '--noprofile', '--norc', '-c',
            '{0} info | grep "^URL: " | sed -e "s/^URL: //"'.format(svnBin)
        ] ).strip()
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
        svn_info = self._callExternal( [ svnBin, 'info' ] ).split("\n")

        for si in svn_info:
            si = si.split( ': ', 1 )
            if si[0] == 'Revision':
                return si[1]
            
        return 'local'



