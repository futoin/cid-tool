
import subprocess

class SubTool:
    def __init__( self, name ) :
        self._name = name
        self._have_tool = False
        
    def _callExternal( self, cmd ) :
        try:
            return subprocess.check_output( cmd )
        except subprocess.CalledProcessError:
            return None
    
    def initEnv( self, env ) :
        name = self._name
        bin_env = name + 'Bin'

        if not env.has_key( bin_env ) :
            tool_path = self._callExternal( [ 'which', name ] )
            if tool_path :
                env[ bin_env ] = tool_path.strip()
                self._have_tool = True
