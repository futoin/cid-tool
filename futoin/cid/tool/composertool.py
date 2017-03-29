
import os

from ..buildtool import BuildTool
from .bashtoolmixin import BashToolMixIn

class composerTool( BashToolMixIn, BuildTool ):
    """Dependency Manager for PHP.
    
Home: https://getcomposer.org/

Auto-detected based on composer.json

Composer is installed in composerDir as single Phar with "composer" name without
extension.
composerDir is equal to user's ~/bin/ folder by default.
"""
    COMPOSER_JSON = 'composer.json'
    
    def _installTool( self, env ):
        composer_dir = env['composerDir']
        php_bin = env['phpBin']
        curl_bin = env['curlBin']
        composer_get = env.get('composerGet', 'https://getcomposer.org/installer')

        self._callBash(
            env,
            'mkdir -p {2} &&  {3} -s {0} | {1} -- --install-dir={2} --filename=composer'
                .format(composer_get, php_bin, composer_dir, curl_bin)
        )

    def updateTool( self, env ):
        self._callExternal([env['composerBin'], 'self-update'])

    def uninstallTool( self, env ):
        os.remove(env['composerBin'])
        self._have_tool = False
        
    def envNames( self ) :
        return [ 'composerDir', 'composerBin', 'composerGet' ]

    def initEnv( self, env ) :
        bin_dir = env['binDir']
        composer_dir = env.setdefault('composerDir', bin_dir)
        composer_bin = env.setdefault('composerBin', os.path.join(composer_dir, 'composer'))

        self._addBinPath( composer_dir )

        self._have_tool = os.path.exists( composer_bin )

    def autoDetect( self, config ) :
        return self._autoDetectByCfg( config, self.COMPOSER_JSON )
    
    def getDeps( self ) :
        return [ 'php', 'curl', 'bash' ]

    def loadConfig( self, config ) :
        content = self._loadJSONConfig( self.COMPOSER_JSON )
        if content is None: return

        for f in ( 'name', 'version' ):
            if f in content and f not in config:
                config[f] = content[f]

    def updateProjectConfig( self, config, updates ) :
        def updater( json ):
            for f in ( 'name', 'version' ):
                if f in updates :
                        json[f] = updates[f]

        return self._updateJSONConfig( self.COMPOSER_JSON, updater, indent=4 )
    
    def onPrepare( self, config ):
        composerBin = config['env']['composerBin']
        self._callExternal( [ composerBin, 'install' ] )
        
    def onPackage( self, config ):
        composerBin = config['env']['composerBin']
        self._callExternal( [ composerBin, 'install', '--no-dev' ] )

