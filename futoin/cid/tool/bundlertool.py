
from ..buildtool import BuildTool
from .gemtoolmixin import GemToolMixIn

class bundlerTool( GemToolMixIn, BuildTool ):
    def autoDetect( self, config ) :
        return self._autoDetectByCfg(
                config,
                [ 'Gemfile' ]
        )

    def onPrepare( self, config ):
        self._callExternal( [ config['env']['bundlerBin'], 'install' ] )
        
    def initEnv( self, env ) :
        super(bundlerTool, self).initEnv( env, 'bundle' )
