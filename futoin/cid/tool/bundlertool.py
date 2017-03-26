
from ..buildtool import BuildTool
from .gemtoolmixin import GemToolMixIn

class bundlerTool( GemToolMixIn, BuildTool ):
    def autoDetect( self, config ) :
        return self._autoDetectByCfg(
                config,
                [ 'Gemfile' ]
        )

    def initEnv( self, env ) :
        super(bundlerTool, self).initEnv( env, 'bundle' )

    def onPrepare( self, config ):
        self._callExternal( [ config['env']['bundlerBin'], 'install' ] )

    def onPackage( self, config ):
        self._callExternal( [ config['env']['bundlerBin'], 'install',
                             '--deployment', '--clean' ] )
