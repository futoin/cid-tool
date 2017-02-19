
from __future__ import print_function

import subprocess
import os
import sys
import json
import hashlib
from collections import OrderedDict

class SubTool:
    TYPE_RUNENV = 'runenv'
    TYPE_RUNTIME = 'runtime'
    TYPE_BUILD = 'build'
    TYPE_VCS = 'vcs'
    TYPE_RMS = 'rms'
    
    def __init__( self, name ) :
        self._name = name
        self._have_tool = False
        
    @classmethod
    def _callExternal( cls, cmd, suppress_fail=False, verbose=True ) :
        try:
            if verbose and not suppress_fail:
                print( 'Call: ' + subprocess.list2cmdline( cmd ), file=sys.stderr )
                stderr = sys.stderr
            else:
                stderr = subprocess.PIPE
            res = subprocess.check_output( cmd, stdin=subprocess.PIPE, stderr=stderr )
            
            try:
                res = str(res, 'utf8')
            except:
                pass
            
            return res
        except subprocess.CalledProcessError as e:
            if suppress_fail :
                return None
            raise e
    
    @classmethod
    def _which( cls, program ):
        "Copied from stackoverflow"
        def is_exe(fpath):
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

        fpath, fname = os.path.split(program)
        if fpath:
            if is_exe(program):
                return program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                path = path.strip('"')
                exe_file = os.path.join(path, program)
                if is_exe(exe_file):
                    return exe_file

        return None

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

    @classmethod
    def addBinPath( cls, bin_dir, first=False ) :
        bin_dir_list = os.environ['PATH'].split(os.pathsep)

        if bin_dir not in bin_dir_list:
            if first :
                bin_dir_list[0:0] = bin_dir
            else :
                bin_dir_list.append(bin_dir)

            os.environ['PATH'] = os.pathsep.join(bin_dir_list)

    @classmethod
    def updateEnvFromOutput( cls, env_to_set ):
        env_to_set = env_to_set.split( "\n" )

        for e in env_to_set:
            if not e: break
            n, v = e.split('=', 1)
            os.environ[n] = v

    def _autoDetectVCS( self, config, vcsDir ) :
        if config.get( 'vcs', None ) == self._name :
            return True
        
        if os.path.isdir( vcsDir ) :
            if config.get( 'vcs', None ) is not None:
                raise RuntimeError( 'Another VCS type has been already detected!' )
            config['vcs'] = self._name
            return True
        
        return False
    
    def _autoDetectRMS( self, config ) :
        if config.get( 'rms', None ) == self._name :
            return True
        
        return False
    
    def _autoDetectByCfg( self, config, file_name ) :
        if self._name in config.get( 'tools', [] ) :
            return True
        
        if type( file_name ) is type( '' ):
            file_name = [ file_name ]

        for f in file_name :
            if os.path.exists( f ) :
                return True
        
        return False
    
    def _installTool( self, env ):
        raise NotImplementedError( "Tool (%s) must be manually installed"  % self._name )
    
    def initEnv( self, env ) :
        name = self._name
        bin_env = name + 'Bin'

        if bin_env not in env :
            tool_path = self._which( name )
            if tool_path :
                env[ bin_env ] = tool_path.strip()
                self._have_tool = True
                
    def getType( self ):
        raise NotImplementedError( self._name )
    
    def autoDetect( self, config ) :
        return False
    
    @classmethod
    def isExternalToolsSetup( cls, env ):
        return env['externalSetup']['installTools']
    
    def requireInstalled( self, env ) :
        self.initEnv( env )

        if not self._have_tool:
            if self.isExternalToolsSetup( env ):
                raise RuntimeError( "Tool (%s) must be installed externally (env config)"  % self._name )
            else :
                self._installTool( env )

            self.initEnv( env )
            
            if not self._have_tool:
                raise RuntimeError( "Failed to install " + self._name )

    def isInstalled( self, env ):
        self.initEnv( env )
        return self._have_tool

    def updateTool( self, env ):
        self.requireInstalled( env )
        
    def uninstallTool( self, env ):
        self._have_tool = False
        raise RuntimeError( "Tool (%s) must be uninstalled externally"  % self._name )

    def loadConfig( self, config ) :
        pass
            
    def getDeps( self ) :
        return []
    
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
    
    def updateProjectConfig( self, config, updates ) :
        """
updates = {
    name : '...',
    version : '...',
}
@return a list of files to be committed
"""
        return []
    
    def vcsCheckout( self, config, branch ):
        raise NotImplementedError( self._name )
    
    def vcsCommit( self, config, message, files ):
        raise NotImplementedError( self._name )
    
    def vcsTag( self, config, tag, message ):
        raise NotImplementedError( self._name )
    
    def vcsPush( self, config, refs ):
        raise NotImplementedError( self._name )
    
    def vcsGetRevision( self, config ) :
        raise NotImplementedError( self._name )
    
    def onPrepare( self, config ):
        pass
    
    def onBuild( self, config ):
        pass
    
    def onPackage( self, config ):
        pass

    def onMigrate( self, config, location ):
        pass
    
    def rmsPromote( self, config, package, rms_pool ):
        raise NotImplementedError( self._name )

    def rmsGetLatest( self, config, rms_pool ):
        raise NotImplementedError( self._name )
    
    def rmsRetrieve( self, config, rms_pool, package ):
        raise NotImplementedError( self._name )


