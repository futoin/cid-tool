
from citool.subtool import SubTool

class bowerTool( SubTool ):
def getType( self ):
        return self.TYPE_BUILD

    def autoDetect( self, config ) :
        return self._autoDetectByCfg( config, 'bower.json' )
    
    def getDeps( self ) :
        return [ 'nodejs' ]

    def updateProjectConfig( self, config, updates ) :
        def updater( json ):
            f = 'name'
            if f in updates :
                    json[f] = updates[f]

        self._updateJSONConfig( 'bower.json', updater )
