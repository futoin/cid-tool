
from __future__ import print_function, absolute_import

import os, json, stat, shutil
from collections import OrderedDict

class UtilMixIn( object ):
    def _updateEnvFromOutput( self, env_to_set ):
        env_to_set = env_to_set.split( "\n" )

        for e in env_to_set:
            if not e: break
            n, v = e.split('=', 1)
            os.environ[n] = v

    def _autoDetectByCfg( self, config, file_name ) :
        if self._name in config.get( 'tools', [] ) :
            return True
        
        if type( file_name ) is type( '' ):
            file_name = [ file_name ]

        for f in file_name :
            if os.path.exists( f ) :
                return True
        
        return False

    def _updateJSONConfig( self, file_name, updater, indent=2, separators=(',', ': ') ) :
        with open(file_name, 'r') as content_file:
            content = content_file.read()
            object_pairs_hook = lambda pairs: OrderedDict( pairs )
            content = json.loads( content, object_pairs_hook=object_pairs_hook )
            
        updater( content )
        
        with open(file_name, 'w') as content_file:
            content =  json.dumps( content, indent=indent, separators=separators )
            content_file.write( content )
            content_file.write( "\n" )
            
        return [ file_name ]
    
    def _updateTextFile( self, file_name, updater ) :
        with open(file_name, 'r') as content_file:
            content = content_file.read()
            
        content = updater( content )
        
        with open(file_name, 'w') as content_file:
            content_file.write( content )
            
        return [ file_name ]
    
    def _isExternalToolsSetup( self, env ):
        return env['externalSetup']['installTools']
    
    def _rmTree( self, dir ):
        os.chmod( dir, stat.S_IRWXU )
        for ( path, dirs, files ) in os.walk( dir ) :
            for id in dirs + files :
                os.chmod( os.path.join( path, id ), stat.S_IRWXU )
        shutil.rmtree(dir)        
