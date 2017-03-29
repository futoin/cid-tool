
from ..buildtool import BuildTool
from .npmtoolmixin import NpmToolMixIn

class gruntTool( NpmToolMixIn, BuildTool ):
    """Grunt: The JavaScript Task Runner.
    
Home: https://gruntjs.com/    

Auto-detected based on Gruntfile.json or Gruntfile.coffee
"""    
    def autoDetect( self, config ) :
        return self._autoDetectByCfg(
                config,
                [ 'Gruntfile.json', 'Gruntfile.coffee' ]
        )

    def _npmName(self):
        return 'grunt-cli'
    
    def onBuild( self, config ):
        gruntBin = config['env']['gruntBin']
        self._callExternal( [ gruntBin ] )
            