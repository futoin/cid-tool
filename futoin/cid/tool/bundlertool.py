
from ..buildtool import BuildTool
from .gemtoolmixin import GemToolMixIn

class bundlerTool( GemToolMixIn, BuildTool ):
    """Bundler: The best way to manage a Ruby application's gems.
    
Home: http://bundler.io/

Auto-detected based on Gemfile.
"""
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
