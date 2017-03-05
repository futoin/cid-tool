
from ..buildtool import BuildTool

# It's more complex tool, but used in build context here
class dockerTool( BuildTool ):
    def autoDetect( self, config ) :
        return self._autoDetectByCfg(
                config,
                [ 'Dockerfile' ]
        )

    def getOrder( self ):
        return 60

    def onBuild( self, config ):
        self._callExternal( [ config['env']['dockerBin'], 'build' ] )
        
