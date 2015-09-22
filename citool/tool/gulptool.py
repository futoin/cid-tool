
from citool.subtool import SubTool

class gulpTool( SubTool ):
    def getType( self ):
        return self.TYPE_BUILD

    def autoDetect( self, config ) :
        return self._autoDetectByCfg( config, 'gulpfile.js' )
    
    def getDeps( self ) :
        return [ 'node' ]

    def _installTool( self ):
        self._callExternal( [ 'npm', 'install', '-g', 'gulp' ] )
    
    def onBuild( self, config ):
        gruntBin = config['env']['gruntBin']
        self._callExternal( [ gruntBin ] )


