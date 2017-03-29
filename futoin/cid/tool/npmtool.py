
import os

from ..buildtool import BuildTool

class npmTool( BuildTool ):
    """npm is the package manager for JavaScript.
    
Home: https://www.npmjs.com/    

Auto-detected based on package.json
"""
    PACKAGE_JSON = 'package.json'
    
    def autoDetect( self, config ) :
        return self._autoDetectByCfg( config, self.PACKAGE_JSON )
    
    def getDeps( self ) :
        return [ 'node' ]
        
    def updateTool( self, env ):
        self._callExternal( [ env['npmBin'], 'update', '-g', 'npm' ] )
        
    def uninstallTool( self, env ):
        pass
    
    def loadConfig( self, config ) :
        content = self._loadJSONConfig( self.PACKAGE_JSON )
        if content is None: return
        
        for f in ( 'name', 'version' ):
            if f in content and f not in config:
                config[f] = content[f]

    def updateProjectConfig( self, config, updates ) :
        def updater( json ):
            for f in ( 'name', 'version' ):
                if f in updates :
                        json[f] = updates[f]

        return self._updateJSONConfig( self.PACKAGE_JSON, updater )
    
    def onPrepare( self, config ):
        if os.path.exists( self.PACKAGE_JSON ):
            npmBin = config['env']['npmBin']
            self._callExternal( [ npmBin, 'install' ] )
        
    def onPackage( self, config ):
        if os.path.exists( self.PACKAGE_JSON ):
            npmBin = config['env']['npmBin']
            self._callExternal( [ npmBin, 'prune', '--production' ] )

