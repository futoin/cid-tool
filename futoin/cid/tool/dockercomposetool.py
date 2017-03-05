
from ..buildtool import BuildTool
from .piptoolmixin import PipToolMixIn

class dockercomposeTool( PipToolMixIn, BuildTool ):
    def autoDetect( self, config ) :
        return self._autoDetectByCfg(
                config,
                [ 'docker-compose.yml' ]
        )
    
    def getDeps( self ) :
        return [ 'pip' ]
        
    def _pipName( self ):
        return 'docker-compose'
    
    def _installTool( self, env ):
        self._requirePythonDev( env )
        super(dockercomposeTool, self)._installTool( env )

    def onBuild( self, config ):
        self._callExternal( [ config['env']['dockercomposeBin'], 'build' ] )
        
    def initEnv( self, env ) :
        super(dockercomposeTool, self).initEnv( env, 'docker-compose' )
