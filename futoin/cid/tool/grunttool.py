
from ..subtool import SubTool

class gruntTool( SubTool ):
    def getType( self ):
        return self.TYPE_BUILD

    def autoDetect( self, config ) :
        return self._autoDetectByCfg(
                config,
                [ 'Gruntfile.json', 'Gruntfile.coffee' ]
        )
    
    def getDeps( self ) :
        return [ 'node', 'npm' ]

    def _installTool( self, env ):
        self._callExternal( [ env['npmBin'], 'install', '-g', 'grunt' ] )
        
    def updateTool( self, env ):
        self._callExternal( [ env['npmBin'], 'update', '-g', 'grunt' ] )
        
    def uninstallTool( self, env ):
        self._callExternal( [ env['npmBin'], 'uninstall', '-g', 'grunt' ] )
        self._have_tool = False

    def onBuild( self, config ):
        gruntBin = config['env']['gruntBin']
        self._callExternal( [ gruntBin ] )
            