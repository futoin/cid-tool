
from ..buildtool import BuildTool

class cmakeTool( BuildTool ):
    def getDeps(self):
        return ['make']

    def getOrder( self ):
        return self.DEFAULT_ORDER - 10

    def autoDetect( self, config ) :
        return self._autoDetectByCfg( config, [
            'CMakeLists.txt'
        ] )
    
    def _installTool( self, env ):
        self._requirePackages(['cmake'])
        self._requireEmerge(['dev-util/cmake'])
        self._requirePacman(['cmake'])
        
    def onBuild( self, config ):
        self._callExternal( [ config['env']['makeBin'] ] )
