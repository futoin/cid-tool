
import os
import re

from ..rmstool import RmsTool

class scpTool( RmsTool ):
    """secure copy."""
    
    REMOTE_PATTERN = '^([a-zA-Z][a-zA-Z0-9_]+@[a-zA-Z][a-zA-Z0-9_]+)(:(.+))?$'
    REMOTE_GRP_USER_HOST = 1
    REMOTE_GRP_PATH = 3
    
    
    def getDeps( self ) :
        return [ 'ssh' ]
    
    def rmsUpload( self, config, rms_pool, package_list ):
        scpBin = config['env']['scpBin']
        rms_repo = config['rmsRepo']
        
        for package in package_list:
            package_basename = os.path.basename( package )
            dst = os.path.join( rms_repo, rms_pool, package_basename )
            self._callExternal( [ scpBin, '-Bq', package, dst ] )
    
    def rmsPromote( self, config, src_pool, dst_pool, package_list ):
        scpBin = config['env']['scpBin']
        rms_repo = config['rmsRepo']
        
        package_list = self.rmsProcessChecksums(config, src_pool, package_list)

        for package in package_list:
            package_basename = os.path.basename( package )
            
            src = os.path.join( rms_repo, src_pool, package_basename )
            dst = os.path.join( rms_repo, dst_pool, package_basename )
            self._callExternal( [ scpBin, '-Bq', src, dst ] )

    def rmsGetList( self, config, rms_pool, package_hint ):
        env = config['env']
        rms_repo = config['rmsRepo']
        result = re.match( self.REMOTE_PATTERN, rms_repo )
        
        if result:
            user_host = result.group( self.REMOTE_GRP_USER_HOST )
            path = os.path.join( result.group( self.REMOTE_GRP_PATH ), rms_pool )
            cmd = 'ls {0}'.format( path )
            ret = self._callExternal( [ env['sshBin'], '-t', user_host, '--', cmd ] ).split("\n")
        else:
            path = os.path.join( rms_repo, rms_pool )  
            ret = os.listdir(path)
    
        return ret
    
    def rmsRetrieve( self, config, rms_pool, package_list ):
        scpBin = config['env']['scpBin']
        
        for package in package_list:
            package_basename = os.path.basename( package )
            src = os.path.join( config['rmsRepo'], rms_pool, package_basename )
            self._callExternal( [ scpBin, '-Bq', src, package_basename ] )
            
    def rmsGetHash(self, config, rms_pool, package, hash_type ):
        env = config['env']
        rms_repo = config['rmsRepo']
        result = re.match( self.REMOTE_PATTERN, rms_repo )
        
        if result:
            user_host = result.group( self.REMOTE_GRP_USER_HOST )
            path = os.path.join( result.group( self.REMOTE_GRP_PATH ), rms_pool )
            cmd = 'ls {0}'.format( path )
            cmd = "{0}sum {1}".format(hash_type, path)
            ret = self._callExternal( [ env['sshBin'], '-t', user_host, '--', cmd ], verbose=False )
        else:
            path = os.path.join( rms_repo, rms_pool, package )  
            ret = self._callExternal( [ hash_type + 'sum', path], verbose=False )
            
        return ret.strip().split()[0]
            
    