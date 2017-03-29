
from ..buildtool import BuildTool
from ..runenvtool import RunEnvTool

class dockerTool( BuildTool, RunEnvTool ):
    """Docker - Build, Ship, and Run Any App, Anywhere.
    
Home: https://www.docker.com/

Experimental support.
"""
    def autoDetect( self, config ) :
        return self._autoDetectByCfg(
                config,
                [ 'Dockerfile' ]
        )

    def getOrder( self ):
        return 10

    def onBuild( self, config ):
        self._callExternal( [ config['env']['dockerBin'], 'build' ] )
        
