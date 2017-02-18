
from citool.subtool import SubTool

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
        npmBin = env['nvmBin']
        self._callExternal( [ npmBin, 'install', '-g', 'grunt' ] )
        
    def updateTool( self, env ):
        npmBin = env['nvmBin']
        self._callExternal( [ npmBin, 'update', '-g', 'grunt' ] )

    def onBuild( self, config ):
        gruntBin = config['env']['gruntBin']
        self._callExternal( [ gruntBin ] )
            