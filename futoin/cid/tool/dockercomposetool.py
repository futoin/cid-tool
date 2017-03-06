
from ..buildtool import BuildTool
from ..runenvtool import RunEnvTool
from .piptoolmixin import PipToolMixIn

class dockercomposeTool( PipToolMixIn, BuildTool, RunEnvTool ):
    def autoDetect( self, config ) :
        return self._autoDetectByCfg(
                config,
                [ 'docker-compose.yml', 'docker-compose.yaml' ]
        )
    
    def getDeps( self ) :
        return [ 'pip', 'docker' ]
    
    def getOrder( self ):
        return self.DEFAULT_ORDER + 20
        
    def _pipName( self ):
        return 'docker-compose'
    
    def _installTool( self, env ):
        self._requirePythonDev( env )
        super(dockercomposeTool, self)._installTool( env )

    def onBuild( self, config ):
        self._callExternal( [ config['env']['dockercomposeBin'], 'build' ] )
        
    def initEnv( self, env ) :
        super(dockercomposeTool, self).initEnv( env, 'docker-compose' )
