
from ..buildtool import BuildTool

class bundleTool( BuildTool ):
    def autoDetect( self, config ) :
        return self._autoDetectByCfg(
                config,
                [ 'Gemfile' ]
        )
    
    def getDeps( self ) :
        return [ 'gem', 'ruby' ]
        
    def _installTool( self, env ):
        self._callExternal( [ env['gemBin'], 'install', 'bundler', '--no-document' ] )
        
    def updateTool( self, env ):
        self._callExternal( [ env['gemBin'], 'update', 'bundler', '--no-document' ] )
        
    def uninstallTool( self, env ):
        self._callExternal( [ env['gemBin'], 'uninstall', 'bundler' ] )
        self._have_tool = False

    def onPrepare( self, config ):
        self._callExternal( [ config['env']['bundleBin'], 'install' ] )
