
from ..buildtool import BuildTool
from .npmtoolmixin import NpmToolMixIn

class gulpTool( NpmToolMixIn, BuildTool ):
    def autoDetect( self, config ) :
        return self._autoDetectByCfg( config, 'gulpfile.js' )
    
    def onBuild( self, config ):
        gruntBin = config['env']['gruntBin']
        self._callExternal( [ gruntBin ] )


