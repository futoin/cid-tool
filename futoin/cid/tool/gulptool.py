
from ..buildtool import BuildTool
from .npmtoolmixin import NpmToolMixIn

class gulpTool( NpmToolMixIn, BuildTool ):
    def autoDetect( self, config ) :
        return self._autoDetectByCfg( config, 'gulpfile.js' )
    
    def onBuild( self, config ):
        self._callExternal( [ config['env']['gulpBin'] ] )


