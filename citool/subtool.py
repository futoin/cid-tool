
import subprocess
import os
import json
from collections import OrderedDict

class SubTool:
    TYPE_RUNENV = 'runenv'
    TYPE_RUNTIME = 'runtime'
    TYPE_BUILD = 'build'
    TYPE_VCS = 'vcs'
    TYPE_RMS = 'rms'
    
    def __init__( self, name ) :
        self._name = name
        self._have_tool = False
        
    def _callExternal( self, cmd ) :
        try:
            return subprocess.check_output( cmd )
        except subprocess.CalledProcessError:
            return None
        
    def _autoDetectVCS( self, config, vcsDir ) :
        if config.get( 'vcs', None ) == self._name :
            return True
        
        if os.path.isdir( vcsDir ) :
            if config.get( 'vcs', None ) is not None:
                raise RuntimeError( 'Another VCS type has been already detected!' )
            config['vcs'] = self._name
            return True
        
        return False
    
    def _autoDetectRMS( self, config ) :
        if config.get( 'rms', None ) == self._name :
            return True
        
        return False
    
    def _autoDetectByCfg( self, config, file_name ) :
        if self._name in config.get( 'tools', [] ) :
            return True
        
        if type( file_name ) is type( '' ):
            file_name = [ file_name ]

        for f in file_name :
            if os.path.exists( f ) :
                return True
        
        return False
    
    def _installTool( self ):
        raise NotImplementedError( "Tool (%s) must be manually installed"  % self._name )
    
    def initEnv( self, env ) :
        name = self._name
        bin_env = name + 'Bin'

        if not env.has_key( bin_env ) :
            tool_path = self._callExternal( [ 'which', name ] )
            if tool_path :
                env[ bin_env ] = tool_path.strip()
                self._have_tool = True
                
    def getType( self ):
        raise NotImplementedError( self._name )
    
    def autoDetect( self, config ) :
        return False
    
    def requireInstalled( self, config ) :
        if not self._have_tool:
            self._installTool()
            self.initEnv( config['env'] )
            
            if not self._have_tool:
                raise RuntimeError( "Failed to install " + self._name )
            
    def loadConfig( self, config ) :
        pass
            
    def getDeps( self ) :
        return []
    
    def _updateJSONConfig( self, file_name, updater, indent=2, separators=(',', ': ') ) :
        with open(file_name, 'r') as content_file:
            content = content_file.read()
            object_pairs_hook = lambda pairs: OrderedDict( pairs )
            content = json.loads( content, object_pairs_hook=object_pairs_hook )
            
        updater( content )
        
        with open(file_name, 'w') as content_file:
            content =  json.dumps( content, indent=indent, separators=separators )
            content_file.write( content )
            content_file.write( "\n" )
            
        return [ file_name ]
    
    def updateProjectConfig( self, config, updates ) :
        """
updates = {
    name : '...',
    version : '...',
}
@return a list of files to be committed
"""
        return []
    
    def vcsCheckout( self, config, branch ):
        raise NotImplementedError( self._name )
    
    def vcsCommit( self, config, message, files ):
        raise NotImplementedError( self._name )
    
    def vcsTag( self, config, tag, message ):
        raise NotImplementedError( self._name )
    
    def vcsPush( self, config, refs ):
        raise NotImplementedError( self._name )
    
    def onPrepare( self, config ):
        pass
    
    def onBuild( self, config ):
        pass
    
    def onPackage( self, config ):
        pass


