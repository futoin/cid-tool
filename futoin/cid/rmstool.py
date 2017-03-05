
from __future__ import print_function, absolute_import

import hashlib

from .subtool import SubTool

__all__ = ['RmsTool']

class RmsTool( SubTool ):
    def autoDetect( self, config ) :
        return self._autoDetectRMS( config )
    
    def rmsPromote( self, config, package, rms_pool ):
        raise NotImplementedError( self._name )

    def rmsGetList( self, config, rms_pool, package_hint ):
        raise NotImplementedError( self._name )
    
    def rmsRetrieve( self, config, rms_pool, package ):
        raise NotImplementedError( self._name )
    
    def _autoDetectRMS( self, config ) :
        if config.get( 'rms', None ) == self._name :
            return True
        
        return False

    @classmethod
    def rmsCalcHash( cls, file_name, hash_type ) :
        hf = hashlib.new( hash_type )
        with open( file_name, 'rb' ) as f:
            for chunk in iter(lambda: f.read(4096), ''):
                if not chunk: break
                hf.update( chunk )
        return "{0}:{1}".format( hash_type, hf.hexdigest() )

    @classmethod
    def rmsVerifyHash( cls, config, file_name ) :
        if config.get('rmsHash', None) is not None:
            ( hash_type, hash_value ) = config['rmsHash'].split(':',1)
            file_hash = cls.rmsCalcHash( file_name, hash_type )
            
            if file_hash != config['rmsHash'] :
                raise RuntimeError(
                        "RMS hash mismatch {0} != {1}".format(
                            file_hash, hash_value ) )
        else :
            file_hash = cls.rmsCalcHash( file_name, 'sha256' )
            
            print( "File: " + file_name )
            print( "Hash: " + file_hash )
            yn = raw_input( "Is it correct? (Y/N) " )
            
            if yn not in ( 'Y', 'y' ):
                raise RuntimeError( 'User abort on RMS hash validation' )


