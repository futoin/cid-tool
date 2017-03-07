
from ..buildtool import BuildTool

class makeTool( BuildTool ):
    def autoDetect( self, config ) :
        return self._autoDetectByCfg( config, [
            'GNUmakefile',
            'makefile',
            'Makefile',
        ] )
    
    def _installTool( self, env ):
            self._requirePackages(['make'])
            self._requireEmerge(['sys-devel/make'])
            self._requirePacman(['make'])

    def onBuild( self, config ):
        self._callExternal( [ config['env']['makeBin'] ] )



