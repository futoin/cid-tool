
from ..buildtool import BuildTool
from ..runenvtool import RunEnvTool

class dockerTool( BuildTool, RunEnvTool ):
    def autoDetect( self, config ) :
        return self._autoDetectByCfg(
                config,
                [ 'Dockerfile' ]
        )

    def getOrder( self ):
        return self.DEFAULT_ORDER + 10

    def onBuild( self, config ):
        self._callExternal( [ config['env']['dockerBin'], 'build' ] )
        
