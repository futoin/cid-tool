
from collections import OrderedDict
import os

class CITool :
    def __init__( self, overrides ) :
        self._overrides = overrides
        self._initConfig()
        
    def tag( self, branch, next_version=None ):
        pass
    
    def prepare( self, vcs_ref ):
        pass
    
    def build( self ):
        pass
    
    def package( self ):
        pass
    
    def promote( self, package, rms_pool ):
        pass
    
    def deploy( self, package, location ):
        pass
    
    def run( self, package=None ):
        pass
    
    def ci_build( self, vcs_ref, rms_pool ):
        pass
    
    def _initConfig( self ):
        self._global_config = gc = self._loadJSON( '/etc/futoin/futoin.json', {'env':{}} )
        self._user_config = uc = self._loadJSON( os.environ.get('HOME','/') + 'futoin.json', {'env':{}} )
        self._project_config = pc = self._loadJSON( 'futoin.json', {} )
        merged = OrderedDict( pc )
        
        if mc.has_key( 'env' ):
            raise InputError( '.env node is set in project config' )
        
        if not uc.has_key( 'env' ) or len( uc ) != 1:
            raise InputError( 'User config must have only .env node' )
        
        if not gc.has_key( 'env' ) or len( gc ) != 1:
            raise InputError( 'Glboal config must have only .env node' )
        
        env = OrderedDict( uc.env )
        
        for ( k, v ) in gc.items():
            if not env.has_key( k ) :
                env[k] = v
            
        merged['env'] = env
        self._config = merged
    
    def _loadJSON( self, file_name, defvalue ):
        try :
            with open(file_name, 'r') as content_file:
                content = content_file.read()
                object_pairs_hook = lambda pairs: OrderedDict( pairs )
                return json.loads( content, object_pairs_hook=object_pairs_hook )
        except IOError:
            return defvalue
            
