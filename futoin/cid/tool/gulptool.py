
from ..buildtool import BuildTool
from .npmtoolmixin import NpmToolMixIn

class gulpTool( NpmToolMixIn, BuildTool ):
    """Automate and enhance your workflow (Node.js).

Home: http://gulpjs.com/    

Auto-detected based on gulpfile.js
"""    
    def autoDetect( self, config ) :
        return self._autoDetectByCfg( config, 'gulpfile.js' )
    
    def onBuild( self, config ):
        self._callExternal( [ config['env']['gulpBin'] ] )


