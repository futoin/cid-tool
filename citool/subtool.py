
import subprocess
import os

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
        
        return os.path.isdir( vcsDir )
    
    def _installTool( self ):
        raise NotImplementedError()
    
    def initEnv( self, env ) :
        name = self._name
        bin_env = name + 'Bin'

        if not env.has_key( bin_env ) :
            tool_path = self._callExternal( [ 'which', name ] )
            if tool_path :
                env[ bin_env ] = tool_path.strip()
                self._have_tool = True
                
    def getType( self ):
        raise NotImplementedError()
    
    def autoDetect( self, config ) :
        return False
    
    def requireInstalled( self, config ) :
        if not self._have_tool:
            self._installTool()
            self.initEnv( config['env'] )
            
            if not self._have_tool:
                raise RuntimeError()
