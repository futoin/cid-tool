
from __future__ import print_function, absolute_import

import os, json, stat, shutil, sys, grp, time, tempfile
from collections import OrderedDict
from ..coloring import Coloring

class UtilMixIn( object ):
    _FUTOIN_JSON = 'futoin.json'
    
    def _updateEnvFromOutput( self, env_to_set ):
        env_to_set = env_to_set.split( "\n" )

        for e in env_to_set:
            if not e: continue
            n, v = e.split('=', 1)
            os.environ[n] = v
            
    def autoDetectFiles( self ):
        return None

    def _autoDetectByCfg( self, config, file_name ) :
        if self._name in config.get( 'toolOrder', [] ) :
            return True
        
        if type( file_name ) is type( '' ):
            file_name = [ file_name ]
            
        root_list = config['projectRootSet']

        for f in file_name :
            if f in root_list :
                return True
        
        return False
    
    #---
    def _loadJSONConfig( self, file_name ):
        if os.path.exists(file_name):
            with open(file_name, 'r') as content_file:
                content = content_file.read()
                object_pairs_hook = lambda pairs: OrderedDict( pairs )
                return json.loads( content, object_pairs_hook=object_pairs_hook )
        else:
            return None
            


    def _updateJSONConfig( self, file_name, updater, indent=2, separators=(',', ': ') ) :
        content = self._loadJSONConfig( file_name )
        
        if content is None:
            return []
            
        updater( content )
        
        self._writeJSONConfig( file_name, content, indent, separators )
            
        return [ file_name ]
    
    def _writeJSONConfig( self, file_name, content, indent=2, separators=(',', ': ')):
        with open(file_name, 'w') as content_file:
            content =  json.dumps( content, indent=indent, separators=separators )
            content_file.write( content )
            content_file.write( "\n" )
    
    #---
    def _readTextFile( self, file_name ) :
        with open(file_name, 'r') as content_file:
            return content_file.read()

    def _updateTextFile( self, file_name, updater ) :
        content = self._readTextFile( file_name )
        content = updater( content )
        self._writeTextFile( file_name, content )
        
        return [ file_name ]
        
    def _writeTextFile( self, file_name, content ):
        with open(file_name, 'w') as content_file:
            content_file.write( content )
    
    def _writeBinaryFile( self, file_name, content ):
        try: content = content.encode(encoding='UTF-8')
        except: pass
    
        with open(file_name, 'wb') as content_file:
            content_file.write( content )
    
    #---
    def _isExternalToolsSetup( self, env ):
        return env['externalSetup']['installTools']
    
    def _rmTree( self, dir ):
        print( Coloring.infoLabel('Removing: ') + Coloring.info(dir),
                file=sys.stderr )
        
        os.chmod( dir, stat.S_IRWXU )
        for ( path, dirs, files ) in os.walk( dir ) :
            for id in dirs + files :
                os.chmod( os.path.join( path, id ), stat.S_IRWXU )
        shutil.rmtree(dir)
        
    def _getTune( self, config, key, default=None ):
        return config.get('toolTune', {}).get(self._name, {}).get(key, default)
    
    def _info( self, msg ):
        print(Coloring.info('INFO: '+msg), file=sys.stderr)
    
    def _warn( self, msg ):
        print(Coloring.warn('WARNING: '+msg), file=sys.stderr)
    
    def _errorExit( self, msg ):
        raise RuntimeError(msg)
        
    def _haveGroup( self, grpname ):
        gid = grp.getgrnam(grpname)[2]
        return gid in os.getgroups()
    
    def _cacheDir( self, key ):
        cache_dir = os.path.join(os.environ['HOME'], '.cache', 'futoin-cid', key)

        try: os.makedirs(cache_dir)
        except: pass
    
        return cache_dir
    
    def _tmpCacheDir( self, **kwargs ):
        tmp_dir = self._cacheDir('tmp')
        
        # do once a day
        base_ts = int(time.time()) - (24*60*60)
        placeholder = os.path.join(tmp_dir, 'cleanup.stamp')
        
        if os.path.exists(placeholder) and os.stat(placeholder).st_mtime > base_ts:
            pass
        else:
            for f in os.listdir(tmp_dir):
                fp = os.path.join(tmp_dir, f)
                s = os.stat(fp)
                
                if s.st_mtime <= base_ts:
                    if stat.S_ISDIR(s.st_mode):
                        self._rmTree(fp)
                    else:
                        os.remove(fp)
            self._writeTextFile(placeholder, '')
        
        return tempfile.mkdtemp(dir = tmp_dir, **kwargs)
            
        
        
        
