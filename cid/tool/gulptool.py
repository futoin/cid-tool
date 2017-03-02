
from cid.subtool import SubTool

class gulpTool( SubTool ):
    def getType( self ):
        return self.TYPE_BUILD

    def autoDetect( self, config ) :
        return self._autoDetectByCfg( config, 'gulpfile.js' )
    
    def getDeps( self ) :
        return [ 'node' ]


    def _installTool( self, env ):
        self._callExternal( [ env['npmBin'], 'install', '-g', 'gulp' ] )
        
    def updateTool( self, env ):
        self._callExternal( [ env['npmBin'], 'update', '-g', 'gulp' ] )
        
    def uninstallTool( self, env ):
        self._callExternal( [ env['npmBin'], 'uninstall', '-g', 'gulp' ] )
        self._have_tool = False

    def onBuild( self, config ):
        gruntBin = config['env']['gruntBin']
        self._callExternal( [ gruntBin ] )


