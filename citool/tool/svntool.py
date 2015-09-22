
from citool.subtool import SubTool
import os

class svnTool( SubTool ):
    def getType( self ):
        return self.TYPE_VCS
    
    def autoDetect( self, config ) :
        return self._autoDetectVCS( config, '.svn' )
    
    def vcsCheckout( self, config, branch ):
        svnBin = config['env']['svnBin']
        wc_dir = config['wcDir']
        svn_repo_path = '%s/branches/%s' % ( config['vcsRepo'], branch )
        
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
        svnBin = config['env']['svnBin']
        svn_url = self._callExternal( [
            'bash', '-c',
            'svn info | grep "^URL: " | sed -e "s/^URL: //"' ] ).strip()
        self._callExternal( [
            svnBin, 'copy',
            '-m', message,
            svn_url,
            '%s/tags/%s' % ( config['vcsRepo'], tag )
        ] )
    
    def vcsPush( self, config, refs ):
        pass
