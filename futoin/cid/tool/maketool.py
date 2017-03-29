
from ..buildtool import BuildTool

class makeTool( BuildTool ):
    """GNU Make.
    
Home: https://www.gnu.org/software/make/

Auto-detected based on 'GNUmakefile', 'makefile' or 'Makefile'.


Expects presence of "clean" target.
Build uses the default target.
"""
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

    def onPrepare( self, config ):
        self._callExternal( [ config['env']['makeBin'], 'clean' ] )

    def onBuild( self, config ):
        self._callExternal( [ config['env']['makeBin'] ] )



