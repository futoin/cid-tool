
from __future__ import print_function, absolute_import

import os
import sys
import subprocess
import importlib
import json
import datetime
import re
import gzip
import shutil
import stat
import time
import fnmatch
import fcntl
import hashlib
from collections import OrderedDict

from .mixins.path import PathMixIn
from .mixins.util import UtilMixIn
from .coloring import Coloring

from .vcstool import VcsTool
from .rmstool import RmsTool
from .buildtool import BuildTool
from .testtool import TestTool
from .migrationtool import MigrationTool
from .runtimetool import RuntimeTool


__all__ = ['CIDTool']

def _call_cmd( cmd ):
    print( Coloring.infoLabel('Call: ') +
            Coloring.info(subprocess.list2cmdline( cmd )),
            file=sys.stderr )

    subprocess.call( cmd, stdin=subprocess.PIPE )    

def cid_action( f ):
    def custom_f( self, *args, **kwargs ) :
        config = self._config

        try:
            fn = f.func_name
        except AttributeError:
            fn = f.__name__

        if fn in config.get('actions', {}) :
            for act in config['actions'][fn] :
                if not isinstance(act, list):
                    act = [act]
                    
                for cmd in act:
                    if cmd == '<default>':
                        f( self, *args, **kwargs )
                    else :
                        _call_cmd( ['sh', '-c', cmd] )
        else :
            f( self, *args, **kwargs )
    return custom_f

class CIDTool( PathMixIn, UtilMixIn ) :
    TO_GZIP = '\.(js|json|css|svg|txt)$'
    VCS_CACHE_DIR = 'vcs'
    
    try:
        _str_type = (str, unicode)
    except NameError:
        _str_type = str
    
    CONFIG_VARS = OrderedDict([
        ('name', _str_type),
        ('version', _str_type),
        ('vcs', _str_type),
        ('vcsRepo', _str_type),
        ('deployBuild', bool),
        ('permissiveChecks', bool),
        ('rms', _str_type),
        ('rmsRepo', _str_type),
        ('rmsPool', _str_type),
        ('tools', dict),
        ('toolTune', dict),
        ('package', list),
        ('packageGzipStatic', bool),
        ('packageChecksums', bool),
        ('persistent', list),
        ('entryPoints', dict),
        ('configenv', dict),
        ('webcfg', dict),
        ('actions', dict),
        ('plugins', dict),
    ])
    
    DEPLOY_LOCK_FILE = '.futoin-deploy.lock'
    GLOBAL_LOCK_FILE = os.path.join(os.environ['HOME'], '.futoin-global.lock')

    def __init__( self, overrides ) :
        self._deploy_lock = None
        self._global_lock = None
        self._startup_env = dict(os.environ)
        self._tool_impl = None
        self._overrides = overrides
        self._initConfig()
        
    def _forEachTool( self, cb, allow_failure=False, base=None ) :
        config = self._config
        tool_impl = self._tool_impl
        tools = config['toolOrder']

        for t in tools :
            t = tool_impl[t]

            if base and not isinstance(t, base):
                continue

            try:
                cb( config, t )
            except RuntimeError as e:
                if not allow_failure:
                    raise e
            
    def _getVcsTool( self ):
        config = self._config
        vcs = config.get('vcs', None)
        
        if not vcs:
            self._errorExit( 'Unknown VCS. Please set through --vcsRepo or project manifest' )
            
        vcstool = self._tool_impl[vcs]
            
        if not config.get('vcsRepo', None): # also check it set
            try:
                config['vcsRepo'] = vcstool.vcsGetRepo( config )
            except subprocess.CalledProcessError as e: pass
            
            if not config.get('vcsRepo', None):
                self._errorExit( 'Unknown VCS repo. Please set through --vcsRepo or project manifest' )

        # Make sure these are present event after config is re-read
        self._overrides['vcs'] = vcs
        self._overrides['vcsRepo'] = config['vcsRepo']
        
        return vcstool

    def _getRmsTool( self ):
        config = self._config
        rms = config.get('rms', None)
        
        if not rms:
            self._errorExit( 'Unknown RMS. Please set through --rmsRepo or project manifest' )
        
        if not config.get('rmsRepo', None): # also check it set
            self._errorExit( 'Unknown RMS repo. Please set through --rmsRepo or project manifest' )
        
        # Make sure these are present event after config is re-read
        self._overrides['rms'] = rms
        self._overrides['rmsRepo'] = config['rmsRepo']
        
        return self._tool_impl[rms]

    def _processWcDir( self ):
        config = self._config
        wcDir = config['wcDir']
        
        if not os.path.exists(wcDir):
            os.makedirs(wcDir)
        
        if wcDir != os.getcwd():
            # Make sure to keep VCS info when switch to another location
            # for checkout.
            #---
            if 'vcs' in config:
                self._getVcsTool()

                for cv in ['vcs', 'vcsRepo']:
                    self._overrides[cv] = config[cv]
            #---

            print( Coloring.infoLabel('Changing to: ') + Coloring.info(wcDir),
                file=sys.stderr )
            os.chdir( wcDir )
            self._overrides['wcDir'] = config['wcDir'] = os.getcwd()
            self._initConfig()

    @cid_action
    def tag( self, branch, next_version=None ):
        mode = 'patch'
        
        if next_version in ['patch', 'minor', 'major']:
            mode = next_version
            next_version = None
        
        if next_version and not re.match('^[0-9]+\.[0-9]+\.[0-9]+$', next_version):
            self._errorExit( 'Valid version format: x.y.z' )
            
        self._processWcDir()
            
        config = self._config
        vcstool = self._getVcsTool()
        vcsrepo = config['vcsRepo']
        
        #---
        self._info('Getting source branch {0} from {1}'.format(branch, vcsrepo))
        vcstool.vcsCheckout( config, branch )
        self._initConfig()
        config = self._config
        
        if 'name' not in config:
            self._errorExit('Failed to detect project "name"')
        
        # Set new version
        if next_version is None:
            if 'version' in config :
                next_version = config['version']
            else :
                self._errorExit( 'current project version is unknown' )

            next_version = next_version.split('.')
            next_version += ['0'] * 3
            del next_version[3:]
            
            if mode == 'patch':
                next_version[2] = str(int(next_version[2]) + 1)
            elif mode == 'minor':
                next_version[1] = str(int(next_version[1]) + 1)
                next_version[2] = '0'
            elif mode == 'major':
                next_version[0] = str(int(next_version[0]) + 1)
                next_version[1] = '0'
                next_version[2] = '0'
                
            next_version = '.'.join( next_version )

        config['version'] = next_version
        
        #---
        self._info('Updating files for release')
        to_commit = []        
        self._forEachTool(
            lambda config, t: to_commit.extend(
                t.updateProjectConfig( config, { 'version' : next_version } )
            )
        )
        
        #---
        if to_commit:
            self._info('Committing updated files')
            message = "Updated for release %s %s" % ( config['name'], config['version'] )
            vcstool.vcsCommit( config, message, to_commit )
        else:
            self._info('Nothing to commit')
        
        #---
        tag = "v%s" % next_version
        self._info('Creating a tag {0}'.format(tag))
        message = "Release %s %s" % ( config['name'], config['version'] )
        vcstool.vcsTag( config, tag, message )

        #---
        self._info('Pushing changes to {0}'.format(vcsrepo))
        vcstool.vcsPush( config, [ branch, tag ] )

    @cid_action
    def prepare( self, vcs_ref ):
        self._processWcDir()
        
        config = self._config

        # make a clean checkout
        if vcs_ref:
            vcstool = self._getVcsTool()

            self._info('Getting source ref {0} from {1}'.format(vcs_ref, config['vcsRepo']))
            vcstool.vcsCheckout( config, vcs_ref )
            self._initConfig()

        #--
        self._info('Running "prepare" in tools')
        self._forEachTool(
            lambda config, t: t.onPrepare( config ),
            base=BuildTool
        )

    @cid_action
    def build( self ):
        self._processWcDir()
        
        self._info('Running "build" in tools')
        self._forEachTool(
            lambda config, t: t.onBuild( config ),
            base=BuildTool
        )

    @cid_action
    def package( self ):
        self._processWcDir()
        
        #---
        self._info('Running "package" in tools')
        self._forEachTool(
            lambda config, t: t.onPackage( config ),
            base=BuildTool
        )
        
        #---
        config = self._config
        package_files = config.get('packageFiles', None)

        if package_files is not None:
            self._info('Found binary artifacts from tools: {0}'.format(package_files))
            self._lastPackages = package_files
            return
        
        # Note: It is assumed that web root is in the package content
        #---
        if config.get('packageGzipStatic', True):
            self._info('Generating GZip files of static content')
            webroot = config.get( 'webcfg', {}).get( 'root', '.' )
            to_gzip_re = re.compile( self.TO_GZIP, re.I )
            
            for ( path, dirs, files ) in os.walk( webroot ) :
                for f in files :
                    if to_gzip_re.search( f ):
                        f = os.path.join( path, f )
                        with open(f, 'rb') as f_in:
                            with gzip.open(f + '.gz', 'wb', 9) as f_out:
                                shutil.copyfileobj(f_in, f_out)
        
        #---
        try:
            package_content = config['package']
        except KeyError:
            package_content = set(os.listdir('.'))
            # TODO: make it more extensible
            package_content -= set(
                fnmatch.filter(package_content, '.git*') +
                fnmatch.filter(package_content, '.hg*') +
                ['.svn']
            )
            package_content = list(package_content)

        if type(package_content) != list:
            package_content = [ package_content ] 

        package_content.sort()
        package_content_cmd = subprocess.list2cmdline( package_content )
        
        self._info('Generating package from {0}'.format(package_content))

        #---
        if config.get('packageChecksums', True):
            self._info('Generating checksums')
            checksums_file = '.package.checksums'
                
            checksums = []
            cs_files = []
            
            for pkg_item in sorted(package_content):
                if os.path.isfile(pkg_item):
                    cs_files.append(pkg_item)

                if os.path.isdir(pkg_item):
                    for ( path, dirs, files ) in os.walk(pkg_item) :
                        for f in sorted(files) :
                            f = os.path.join( path, f )
                            cs_files.append(f)
                        
            for cf in cs_files:
                hasher = hashlib.sha512()

                with open(cf, 'rb') as f_in:
                    for chunk in iter(lambda: f_in.read(65536), b""):
                        hasher.update(chunk)

                checksums.append("{0}  {1}".format(hasher.hexdigest(), cf))
                
            checksums.append('')

            with open(checksums_file, 'w') as f_out:
                f_out.write("\n".join(checksums))
                
            try:
                package_content.index( '.' )
            except ValueError:
                package_content.append( checksums_file )
        
        #---
        buildTimestamp = datetime.datetime.utcnow().strftime( '%Y%m%d%H%M%S' )
        name = config.get('name', 'UNKNOWN').split('/')[-1]
        version = config.get('version', 'UNKNOWN')
        vcs_ref = config.get( 'vcsRef', None )
        
        # Note: unless run in clean ci_build process,
        # all builds must be treated as snapshots/CI builds
        if vcs_ref == 'v' + version :
            package_file = '{0}-{1}-{2}'.format(
                    name, version, buildTimestamp )
        else:
            vcs_ref = 'UNKNOWN'
            
            if config.get('vcs', None):
                try:
                    vcstool = self._getVcsTool()
                    vcs_ref = vcstool.vcsGetRevision( config )
                except subprocess.CalledProcessError as e:
                    if config.get('vcsRepo', None):
                        raise e
                
            package_file = '{0}-CI-{1}-{2}-{3}'.format(
                    name, version, buildTimestamp, vcs_ref )

        if 'target' in config:
            package_file += '-{0}'.format( config['target'] )
            
        package_file += '.txz'
        self._info('Creating package {0}'.format(package_file))
        _call_cmd( ['tar', 'cJf', package_file,
                    '--exclude=' + package_file,
                    '--exclude=.git*',
                    '--exclude=.hg*',
                    '--exclude=.svn'] + package_content )
        # note, no --exclude-vcs
        self._lastPackages = [package_file]
    
    @cid_action
    def check( self ):
        self._processWcDir()
        
        self._info('Running "check" in tools')
        self._forEachTool(
            lambda config, t: t.onCheck( config ),
            allow_failure = self._config.get('permissiveChecks', False),
            base=TestTool
        )

    @cid_action
    def promote( self, package, rms_pool ):
        config = self._config
        rmstool = self._getRmsTool()
        
        self._info('Promoting {0} package to {1} pool'.format(package, rms_pool))
        rmstool.rmsPromote( config, package, rms_pool )
        
    @cid_action
    def migrate( self, location ):
        self._processWcDir()
        
        self._info('Running "migrate" in tools')
        self._forEachTool(
            lambda config, t: t.onMigrate( config, location ),
            base=MigrationTool
        )
        
    def _lockCommon( self, lock, file, flags ):
        assert self.__dict__[lock] is None
        self.__dict__[lock] = os.open(file, os.O_WRONLY|os.O_CREAT)
        try:
            fcntl.flock(self.__dict__[lock], flags)
        except Exception as e:
            self._errorExit('FAILED to acquire{0}: {1}'.format(lock.replace('_', ' '), e))
    
    def _unlockCommon( self, lock ):
        fcntl.flock(self.__dict__[lock], fcntl.LOCK_UN)
        os.close(self.__dict__[lock])
        self.__dict__[lock] = None
        
    def _deployLock( self ):
        self._lockCommon(
            '_deploy_lock',
            os.path.join(self._config['deployDir'], self.DEPLOY_LOCK_FILE),
            fcntl.LOCK_EX | fcntl.LOCK_NB
        )
    
    def _deployUnlock( self ):
        self._unlockCommon('_deploy_lock')
        
    def _globalLock( self ):
        self._lockCommon('_global_lock', self.GLOBAL_LOCK_FILE, fcntl.LOCK_EX)
    
    def _globalUnlock( self ):
        self._unlockCommon('_global_lock')
    
    @cid_action
    def deploy( self, mode, p1, p2=None ):
        # Get to deploy folder
        deploy_dir = self._config['deployDir']
        
        if not deploy_dir:
            deploy_dir = os.path.realpath('.')
            self._overrides['deployDir'] = deploy_dir
            self._initConfig()
        
        self._info('Using {0} as deploy directory'.format(deploy_dir))

        placeholder = os.path.join(deploy_dir, self.DEPLOY_LOCK_FILE)

        if not os.path.exists( deploy_dir ) :
            self._info('Creating deploy directory')
            os.makedirs( deploy_dir )
            open(placeholder, 'w').close()
        elif not os.path.exists(placeholder) and os.listdir(deploy_dir):
            self._errorExit(
                "Deployment dir '{0}' is missing safety placeholder {1}."
                .format(deploy_dir, os.path.basename(placeholder))
            )

        print( Coloring.infoLabel('Changing to: ') + Coloring.info(deploy_dir),
            file=sys.stderr )
        os.chdir( deploy_dir )

        self._deployLock()
        
        if mode == 'rms':
            self._rms_deploy(p1, p2)
        elif mode == 'vcsref':
            self._vcsref_deploy(p1)
        elif mode == 'vcstag':
            self._vcstag_deploy(p1)
        else:
            self._errorExit( 'Not supported deploy mode: ' + mode )
            
        self._deployUnlock()
        
    def _redeployExit( self, deploy_type ):
        self._warn( deploy_type + " has been already deployed. Use --redeploy.")
        sys.exit(0)
        
    def _rms_deploy( self, rms_pool, package=None ):
        config = self._config
        rmstool = self._getRmsTool()

        # Find out package to deploy
        self._info('Finding package in RMS')
        package_list = rmstool.rmsGetList( config, rms_pool, package )

        if package:
            package_list = fnmatch.filter(package_list, package)
            
        if not package_list:
            self._errorExit( "No package found" )
            
        package = self._getLatest(package_list)
        self._info('Found package {0}'.format(package))
            
        # cleanup first, in case of incomplete actions
        self._info('Pre-cleanup of deploy directory')
        self._deployCleanup( [package] )

        # Prepare package name components
        package_basename = os.path.basename( package )
        ( package_noext, package_ext ) = os.path.splitext( package_basename )
        
        # Check if already deployed:
        if os.path.exists( package_noext ):
            if config['reDeploy']:
                self._warn('Forcing re-deploy of the package')
            else:
                self._redeployExit('Package')
        
        # Retrieve package, if not available
        if not os.path.exists( package_basename ) :
            self._info('Retrieving the package')
            rmstool.rmsRetrieve( config, rms_pool, package )
            
        package_noext_tmp = package_noext + '.tmp'
        
        # Prepare temporary folder
        os.mkdir( package_noext_tmp )
        
        # Unpack package to temporary folder
        self._info('Extracting the package')
        if package_ext == '.txz':
            _call_cmd( ['tar', 'xJf', package_basename, '-C', package_noext_tmp ] )
        elif package_ext == '.tbz2':
            _call_cmd( ['tar', 'xjf', package_basename, '-C', package_noext_tmp ] )
        elif package_ext == '.tgz':
            _call_cmd( ['tar', 'xzf', package_basename, '-C', package_noext_tmp ] )
        elif package_ext == '.tar':
            _call_cmd( ['tar', 'xf', package_basename, '-C', package_noext_tmp ] )
        else:
            self._errorExit('Not supported package format: ' + package_ext)
        
        # Common processing
        self._deployCommon( package_noext_tmp, package_noext, [package] )
        
    def _vcsref_deploy( self, vcs_ref ):
        config = self._config
        vcstool = self._getVcsTool()

        # Find out package to deploy
        self._info('Getting the latest revision of {0}'.format(vcs_ref))
        vcs_cache = os.path.realpath(self.VCS_CACHE_DIR)
        rev = vcstool.vcsGetRefRevision( config, vcs_cache, vcs_ref )
            
        if not rev:
            self._errorExit( "No VCS refs found")
            
        target_dir = vcs_ref.replace(os.sep, '_').replace(':', '_')
        target_dir += '__' + rev
            
        # cleanup first, in case of incomplete actions
        self._info('Pre-cleanup of deploy directory')
        self._deployCleanup( [vcs_cache, target_dir] )
        
        # Check if already deployed:
        if os.path.exists( target_dir ):
            if config['reDeploy']:
                self._warn('Forcing re-deploy of the VCS ref')
            else:
                self._redeployExit('VCS ref')
           
        # Retrieve tag
        self._info('Retrieving the VCS ref')
        target_tmp = target_dir + '.tmp'
        # Note: acceptable race condition is possible: vcs_ref
        # may get updated after we get its revision and before
        # we do actual export
        vcstool.vcsExport( config, vcs_cache, vcs_ref, target_tmp )

        # Common processing
        self._deployCommon( target_tmp, target_dir, [vcs_cache] )      

    def _vcstag_deploy( self, vcs_ref ):
        config = self._config
        vcstool = self._getVcsTool()

        # Find out package to deploy
        self._info('Finding tag in VCS')
        vcs_cache = os.path.realpath(self.VCS_CACHE_DIR)
        tag_list = vcstool.vcsListTags( config, vcs_cache, vcs_ref )

        if vcs_ref:
            tag_list = fnmatch.filter(tag_list, vcs_ref)
            
        if not tag_list:
            self._errorExit( "No tags found" )
            
        vcs_ref = self._getLatest(tag_list)
        target_dir = vcs_ref.replace(os.sep, '_').replace(':', '_')
        self._info('Found tag {0}'.format(vcs_ref))
            
        # cleanup first, in case of incomplete actions
        self._info('Pre-cleanup of deploy directory')
        self._deployCleanup( [vcs_cache, target_dir] )
        
        # Check if already deployed:
        if os.path.exists( target_dir ):
            if config['reDeploy']:
                self._warn('Forcing re-deploy of the VCS tag')
            else :
                self._redeployExit('VCS tag')
           
        # Retrieve tag
        self._info('Retrieving the VCS tag')
        vcs_ref_tmp = target_dir + '.tmp'
        vcstool.vcsExport( config, vcs_cache, vcs_ref, vcs_ref_tmp )

        # Common processing
        self._deployCommon( vcs_ref_tmp, target_dir, [vcs_cache] )        
        
    def _versionSort( self, verioned_list ):
        def castver(v):
            res = re.split(r'[\W_]+', v)
            for (i, vc) in enumerate(res):
                try: res[i] = int(vc, 10)
                except: pass
            return res
            
        verioned_list.sort(key=castver)

    def _getLatest( self, verioned_list ):
        self._versionSort(verioned_list)
        return verioned_list[-1]

    def _deployCommon( self, tmp, dst, cleanup_whitelist ):
        config = self._config
        config['wcDir'] = os.path.realpath(tmp)
        
        # Setup persistent folders
        self._info('Setting up read-write directories')
        persistent_dir = os.path.abspath( config['env'].get('persistentDir', 'persistent') )
        wdir_wperm = stat.S_IRUSR | stat.S_IXUSR | \
                    stat.S_IRGRP | stat.S_IXGRP | \
                    stat.S_IWUSR | stat.S_IWGRP
        
        for d in config.get('persistent', []) :
            pd = os.path.join( persistent_dir, d )
            dd = os.path.join( tmp, d )

            if not os.path.isdir( pd ) :
                os.makedirs( pd, wdir_wperm )
                
            if os.path.exists( dd ):
                shutil.copytree( dd, pd )
                self._rmTree( dd )
            
            os.symlink( pd, dd )
        
                
        # Build
        if config.get('deployBuild', False):
            self._info('Building project in deployment')
            self.prepare(None)
            self.build()
            
        # Complete migration
        self.migrate( tmp )
        
        # return back
        os.chdir(config['deployDir'])
            
        # Setup read-only permissions
        self._info('Setting up read-only permissions')
        dir_perm = stat.S_IRUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP
        file_perm = stat.S_IRUSR | stat.S_IRGRP
        walk_list = os.walk( tmp )
        os.chmod( tmp, dir_perm )
        
        for ( path, dirs, files ) in walk_list :
            for d in dirs :
                os.chmod( os.path.join( path, d ), dir_perm )
            for f in files :
                os.chmod( os.path.join( path, f ), file_perm )
        
        # Setup per-user services
        self._deployServices( tmp )
        
        # Move in place
        self._info('Switching current deployment')
        if os.path.exists( dst ):
            # re-deploy case
            os.rename( dst, dst + '.tmprm' )

        os.rename( tmp, dst )
        os.symlink( dst, 'current.tmp' )
        os.rename( 'current.tmp', 'current' )
        
        # Re-run
        self._reloadServices()
        
        # Cleanup old packages and deploy dirs
        self._info('Post-cleanup of deploy directory')
        self._deployCleanup( cleanup_whitelist )
        
    def _deployCleanup( self, whitelist ):
        if os.path.exists('current'):
            whitelist.append( os.path.basename(os.readlink('current')) )
            
        whitelist += ['current', 'persistent', self.DEPLOY_LOCK_FILE]

        for f in os.listdir( '.' ):
            ( f_noext, f_ext ) = os.path.splitext( f )
            
            if f in whitelist:
                continue
            
            if os.path.isdir(f):
                self._rmTree(f)
            else:
                os.chmod( f, stat.S_IRWXU )
                os.remove( f )
            
            
    def _deployServices( self, subdir ):
        pass
    
    def _reloadServices( self ):
        pass
    
    def run( self, command, args ):
        self._processWcDir()
        
        config = self._config
        entry_points = config.get('entryPoints', {})
        actions = config.get('actions', {})
        args = args or []
        
        if command:
            if command in entry_points:
                ep = entry_points[command]
                
                # Do stuff required to get the tool ready
                tool = ep['tool']
                self._overrides['tool'] = tool
                self._initConfig()
                
                # 
                config = self._config
                t = self._tool_impl[tool]
                
                if isinstance(t, RuntimeTool):
                    t.onRun(config, ep['file'], args, ep.get('tune', {}))
                else:
                    self._errorExit('Tool "{0}" for "{1}" does not support "run" command'.format(tool, command))
                
            elif command in actions:
                act = actions[command]
                
                if not isinstance(act, list):
                    act = [act]
                
                for cmd in act:
                    _call_cmd( ['sh', '-c', '{0} {1}'.format(
                        cmd, subprocess.list2cmdline(args)
                    )] )
            else:
                self._errorExit('Unknown "{0}" action or entry point'.format(command))
        else:
            for cmd in entry_points:
                pid = os.fork()

                if not pid:
                    sys.stdin.close()
                    sys.stdin = open(os.devnull, 'r')
                    self.run(cmd, None)
                    
            i = len(entry_points)
            
            while i > 0:
                os.wait()
                i -= 1
                   
    @cid_action
    def ci_build( self, vcs_ref, rms_pool ):
        config = self._config
        wcDir = config['wcDir']

        if os.path.exists( wcDir ) and wcDir != os.getcwd():
            try:
                dst = '{0}.bak{1}'.format(wcDir, int(time.time()))
                print( Coloring.infoLabel('Renaming: ') +
                       Coloring.info(wcDir + ' to ' + dst ),
                       file=sys.stderr )
                os.rename( wcDir, dst )
            except OSError:
                self._rmTree( wcDir )
        
        self._lastPackages = None
        self.prepare( vcs_ref )
        self.build()
        self.package()
        self.check()
        
        if rms_pool and self._lastPackages:
            if config.get('actions', {}).get('promote', None):
                for p in self._lastPackages:
                    self.promote( p, rms_pool )
            else:
                self._info('Promoting package(s) to {0} pool'.format(rms_pool))
                rmstool = self._getRmsTool()
                rmstool.rmsPromoteMany( config, self._lastPackages, rms_pool )

    def tool_exec( self, tool, args ):
        t = self._tool_impl[tool]
        t.onExec(self._config['env'], args)
    
    def tool_install( self, tool ):
        config = self._config
        env = config['env']
        
        if self._isExternalToolsSetup( env ):
            self._errorExit('environment requires external installation of tools')

        if tool :
            tools = [tool]
        else :
            tools = config['toolOrder']
            
        self._globalLock()

        for tool in tools:
            t = self._tool_impl[tool]
            t.requireInstalled( env )
            
        self._globalUnlock()

    def tool_uninstall( self, tool ):
        config = self._config
        env = config['env']
        
        if self._isExternalToolsSetup( env ):
            self._errorExit('environment requires external management of tools')

        if tool :
            tools = [tool]
        else :
            tools = reversed(config['toolOrder'])
            
        self._globalLock()

        for tool in tools:
            t = self._tool_impl[tool]
            if t.isInstalled( env ):
                t.uninstallTool( env )
                
        self._globalUnlock()

    def tool_update( self, tool ):
        config = self._config
        env = config['env']
        
        if self._isExternalToolsSetup( env ):
            self._errorExit('environment requires external management of tools')

        if tool :
            tools = [tool]
        else :
            tools = config['toolOrder']
            
        self._globalLock()

        for tool in tools:
            t = self._tool_impl[tool]
            t.updateTool( env )
            
        self._globalUnlock()

    def tool_test( self, tool ):
        config = self._config
        env = config['env']

        if tool :
            tools = [tool]
        else :
            tools = config['toolOrder']

        for tool in tools:
            t = self._tool_impl[tool]
            
            if not t.isInstalled( env ) :
                self._errorExit( "Tool '%s' is missing" % tool )
                
    def tool_env( self, tool ):
        config = self._config
        env = config['env']

        if tool :
            tools = [tool]
        else :
            tools = config['toolOrder']
            
        res = dict(os.environ)
        
        # remove unchanged vars
        for k, v in self._startup_env.items():
            if res.get(k, None) == v:
                del res[k]

        for tool in tools:
            self._tool_impl[tool].exportEnv(env, res)
            
        for k, v in sorted(res.items()):
            if type(v) == type(''):
                v = v.replace("'", "\\'").replace('\\', '\\\\')
            elif not v:
                v = ''
            print("{0}='{1}'".format(k, v))

    def _tool_cmd( self, tool, base, method ):
        config = self._config
        env = config['env']

        t = self._tool_impl[tool]

        if isinstance(t, base):
            t.loadConfig( config ) # see self._initTools()
            getattr( t, method )( config )
        else:
            self._errorExit('{0} tool does not support {1}'.format(tool, method))
        
    def tool_prepare( self, tool ):
        self._tool_cmd( tool, BuildTool, 'onPrepare' )

    def tool_build( self, tool ):
        self._tool_cmd( tool, BuildTool, 'onBuild' )

    def tool_check( self, tool ):
        self._tool_cmd( tool, TestTool, 'onCheck' )

    def tool_package( self, tool ):
        self._tool_cmd( tool, BuildTool, 'onPackage' )
        
        package_files = self._config.get('packageFiles', None)
        
        if package_files is not None:
            self._info('Package files: {0}'.format(package_files))

    def tool_migrate( self, tool ):
        self._tool_cmd( tool, MigrationTool, 'onMigrate' )

    def tool_list( self ):
        print("List of tools supported by CID:")
        for k in sorted(self._tool_impl.keys()):
            t = self._tool_impl[k]
            doc = t.__doc__.strip() or Coloring.warn('!! Missing documentation.')
            doc = doc.split("\n")[0]
            print(Coloring.infoLabel("  * " + k + ': ') + Coloring.info(doc))
        print('End.')

    def tool_describe( self, tool ):
        t = self._tool_impl[tool]
        
        print(Coloring.infoLabel('* Tool: ') + Coloring.warn(tool))
        
        auto_detect = t.autoDetectFiles()
        if auto_detect:
            if not isinstance(auto_detect, list):
                auto_detect = [auto_detect]
            print(Coloring.infoLabel('* Auto-detection (files): ') + ', '.join(auto_detect))
        
        if isinstance(t, VcsTool):
            print(Coloring.infoLabel('* Auto-detected, if set as VCS '))

        if isinstance(t, RmsTool):
            print(Coloring.infoLabel('* Auto-detected, if set as RMS '))
        
        env_vars = t.envNames()
        if env_vars:
            print(Coloring.infoLabel('* Environment variables: ') + ', '.join(env_vars))

        deps = t.getDeps()
        if deps:
            print(Coloring.infoLabel('* Dependencies: ') + ', '.join(deps))

        rdeps = t.getPostDeps()
        if rdeps:
            print(Coloring.infoLabel('* Reverse dependencies: ') + ', '.join(rdeps))
            
        order = t.getOrder()
        if order:
            print(Coloring.infoLabel('* Order shift: ') + str(order))

        print()
        doc = t.__doc__.strip() or Coloring.warn('!! Missing documentation.')
        print(Coloring.info(doc))
        print()
        
    def tool_detect( self ):
        config = self._config
        env = config['env']

        for t in config['toolOrder']:
            ver = env.get(t+'Ver', None)
            
            if ver:
                print("{0}={1}".format(t, ver))
            else:
                print(t)

    def init_project( self, project_name ):
        self._processWcDir()

        if os.path.exists(self._FUTOIN_JSON):
            self._errorExit('futoin.json already exists in project root')

        config = self._config
        new_config = OrderedDict()
        
        if project_name:
            new_config['name'] = project_name
        elif 'name' not in config:
            new_config['name'] = os.path.basename(config['wcDir'])
        
        for cv in self.CONFIG_VARS:
            try:
                val = config[cv]

                if val is not None and cv not in new_config:
                    new_config[cv] = val
            except KeyError:
                pass
        
        self._writeJSONConfig(self._FUTOIN_JSON, new_config)
        
    def vcs_checkout( self, vcs_ref ):
        self._processWcDir()

        config = self._config
        vcstool = self._getVcsTool()

        self._info('Getting source ref {0} from {1}'.format(vcs_ref, config['vcsRepo']))
        vcstool.vcsCheckout( config, vcs_ref )

    def vcs_commit( self, msg, files ):
        self._processWcDir()
        
        config = self._config
        vcstool = self._getVcsTool()

        if files:
            self._info('Committing: ' + ', '.join(files))
        else:
            self._info('Committing updated files')
        vcstool.vcsCommit( config, msg, files )
        
        self._info('Pushing changes to {0}'.format(config['vcsRepo']))
        vcstool.vcsPush( config, None )

    def vcs_branch( self, vcs_ref ):
        self._processWcDir()
        
        config = self._config
        vcstool = self._getVcsTool()

        self._info('Creating new branch {0} in {1}'.format(vcs_ref, config['vcsRepo']))
        vcstool.vcsBranch( config, vcs_ref )
        
    def vcs_merge( self, vcs_ref, cleanup=True ):
        self._processWcDir()
        
        config = self._config
        vcstool = self._getVcsTool()

        self._info('Merging branch {0} from {1}'.format(vcs_ref, config['vcsRepo']))
        vcstool.vcsMerge( config, vcs_ref, cleanup )

    def vcs_delete( self, vcs_ref, vcs_cache_dir ):
        self._processWcDir()
        
        config = self._config
        vcstool = self._getVcsTool()

        self._info('Deleting branch {0} from {1}'.format(vcs_ref, config['vcsRepo']))
        vcstool.vcsDelete( config, vcs_cache_dir, vcs_ref )
        
    def vcs_export( self, vcs_ref, dst_path, vcs_cache_dir ):
        if os.path.exists(dst_path):
            if os.listdir(dst_path):
                self._errorExit('Destination directory {0} exists and is not empty'.format(dst_path))
        else:
            os.makedirs(dst_path)
            
        self._processWcDir()

        config = self._config
        vcstool = self._getVcsTool()

        self._info('Export ref {0} from {1}'.format(vcs_ref, config['vcsRepo']))
        vcstool.vcsExport( config, vcs_cache_dir, vcs_ref, dst_path )

    def vcs_tags( self, tag_hint, vcs_cache_dir ):
        self._processWcDir()

        config = self._config
        vcstool = self._getVcsTool()

        tag_list = vcstool.vcsListTags( config, vcs_cache_dir, tag_hint )
        
        if tag_hint:
            tag_list = fnmatch.filter(tag_list, tag_hint)
            
        self._versionSort(tag_list)
        
        print("\n".join(tag_list))
        
    def vcs_branches( self, branch_hint, vcs_cache_dir ):
        self._processWcDir()

        config = self._config
        vcstool = self._getVcsTool()

        branch_list = vcstool.vcsListBranches( config, vcs_cache_dir, branch_hint )
        
        if branch_hint:
            branch_list = fnmatch.filter(branch_list, branch_hint)
            
        self._versionSort(branch_list)
        
        print("\n".join(branch_list))

    def vcs_reset( self ):
        self._processWcDir()

        config = self._config
        vcstool = self._getVcsTool()

        self._info('Reverting all local changes')
        vcstool.vcsRevert( config )
        
    def vcs_ismerged( self, vcs_ref ):
        self._processWcDir()
        
        config = self._config
        vcstool = self._getVcsTool()

        if vcstool.vcsIsMerged( config, vcs_ref ):
            self._info('Branch {0} is merged'.format(vcs_ref))
        else :
            self._info('Branch {0} is NOT merged'.format(vcs_ref))
            sys.exit(1)

    def _initConfig( self ):
        user_home = os.environ.get('HOME','/')
        user_config_path = os.path.join( user_home, '.' + self._FUTOIN_JSON )
        
        if not os.path.exists(user_config_path) and user_home != self._overrides['wcDir']:
            user_config_path = os.path.join( user_home, self._FUTOIN_JSON )
        
        self._global_config = gc = self._loadJSON( os.path.join('/', 'etc', 'futoin', self._FUTOIN_JSON), {'env':{}} )
        self._user_config = uc = self._loadJSON( user_config_path, {'env':{}} )
        self._project_config = pc = self._loadJSON( self._FUTOIN_JSON, {} )

        deploy_dir = self._overrides.get( 'deployDir', None )
        dc = {}
        if deploy_dir :
            dc = self._loadJSON( os.path.join( deploy_dir, self._FUTOIN_JSON ), dc )
        self._deploy_config = dc
        
        config = OrderedDict( pc )
        self._sanitizeConfig( config )
        
        if 'env' in pc:
            self._errorExit('.env node must not be set in project config')

        if 'env' not in dc:
            dc['env'] = {}
        
        if 'env' not in uc or len( uc ) != 1:
            self._errorExit('User config must have the only .env node')
        
        if 'env' not in gc or len( gc ) != 1:
            self._errorExit('Global config must have the only .env node')
        
        env = OrderedDict( dc['env'] )
        
        for ( k, v ) in uc['env'].items():
            env.setdefault( k, v )
        for ( k, v ) in gc['env'].items():
            env.setdefault( k, v )

        self._initEnv( env )

        # Deployment config can override project config
        for (k, v) in dc.items():
            config[k] = v

        config['env'] = env
        config.update( self._overrides )
        self._config = config
        
        self._initTools()
        
    def _sanitizeConfig( self, config ):
        conf_vars = self.CONFIG_VARS
        
        for (k, v) in config.items():
            if k not in conf_vars:
                self._warn('Removing unknown config variable "{0}"'.format(k))
                del config[k]
            elif not isinstance(v, conf_vars[k]):
                req_t = conf_vars[k]
                if isinstance(req_t, tuple):
                    req_t = req_t[0]
                    
                self._errorExit(
                    'Config variable "{0}" type "{1}" is not instance of "{2}"'
                    .format(k, v.__class__.__name__, req_t[0].__name__)
                )

        #---
        # Make sure futoinTool is enabled, if futoin.json is present.
        # Otherwise, auto-detection gets disabled and futoin.json is not updated
        tools = config.get('tools', None)

        if tools and 'futoin' not in tools:
            tools['futoin'] = True
        
        #---
        entry_points = config.get('entryPoints', None)

        if entry_points:
            for (en, ep) in entry_points.items():
                for k in ['tool', 'file']:
                    if k not in ep:
                        self._errorExit('Entry point "{0}" is missing "{1}"'.format(en, k))
                if 'tune' in ep and not isinstance(ep['tune'], dict):
                    self._errorExit('Entry point "{0}" has invalid tune parameter'.format(en))
        
        #---
        toolTune = config.get('toolTune', None)
        
        if toolTune:
            for (tn, tune) in toolTune.items():
                if not isinstance(tune, dict):
                    self._errorExit('Tool tune "{0}" is not of map type'.format(tn))
        
        #---
    
    def _loadJSON( self, file_name, defvalue ):
        try :
            with open(file_name, 'r') as content_file:
                content = content_file.read()
                object_pairs_hook = lambda pairs: OrderedDict( pairs )
                return json.loads( content, object_pairs_hook=object_pairs_hook )
        except IOError:
            return defvalue
        
    def _initEnv( self, env ) :
        env.setdefault( 'type', 'dev' )
        env.setdefault( 'startup', 'cron' )
        env.setdefault( 'webServer', 'nginx' )
        env.setdefault( 'vars', {} )
        env.setdefault( 'mainConfig', {} )
        env.setdefault( 'plugins', {} )

        env.setdefault( 'externalSetup', {} )
        externalSetup = env['externalSetup']
        externalSetup.setdefault( 'runCmd', None )
        externalSetup.setdefault( 'webServer', False )
        externalSetup.setdefault( 'startup', False )
        externalSetup.setdefault( 'installTools', False )

        env.setdefault( 'binDir', os.path.join(os.environ['HOME'], 'bin') )
        self._addBinPath( env['binDir'] )
        
    def _checkKnownTool(self, tool, tool_impl=None):
        if tool_impl is None:
            tool_impl = self._tool_impl
        
        if tool not in tool_impl:
            self._errorExit('Implementation for "{0}" was not found'.format(tool))

    def _initTools( self ):
        config = self._config
        env = config['env']
        
        #---
        config['projectRootSet'] = set(os.listdir('.'))

        #---
        tool_impl = self._tool_impl
        
        if tool_impl is None:
            tool_impl = {}
            default_tool_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'tool'
            )
            
            tool_files = os.listdir(default_tool_dir)
            tool_files = fnmatch.filter(tool_files, '*tool.py')

            for f in tool_files:
                k = f.replace('tool.py', '')
                pkg = 'futoin.cid.tool.' + k + 'tool'
                m = importlib.import_module( pkg )
                tool_impl[ k ] = getattr( m, k + 'Tool' )( k )

            self._tool_impl = tool_impl
            
        plugins = env['plugins'].copy()
        plugins.update( config.get( 'plugins', {} ) )
        
        for ( k, v ) in plugins.items() :
            if k not in tool_impl:
                m = importlib.import_module( v )
                tool_impl[ k ] = getattr( m, k + 'Tool' )( k )

        #---
        curr_tool = config.get('tool', None)
        
        if curr_tool:
            tools = [ curr_tool ]
            tool_ver = config.get('toolVer', None)
            
            if tool_ver:
                config['env'][curr_tool + 'Ver'] = tool_ver
        else :
            config_tools = config.get('tools', {})
            tools = []
            
            if config_tools:
                if not isinstance(config_tools, dict):
                    self._errorExit('futoin.json:tools must be a map of tool=>version pairs')

                for (tool, v) in config_tools.items():
                    self._checkKnownTool(tool, tool_impl)
                    tools.append( tool )

                    if v != '*' and v != True:
                        env[tool + 'Ver'] = v
            else :
                for ( n, t ) in tool_impl.items():
                    if t.autoDetect( config ) :
                        tools.append( n )

            # Make sure deps & env are processed for cli-supplied tools
            #--
            for (item, base) in {'rms' : RmsTool, 'vcs' : VcsTool}.items():
                tool = config.get(item, None)

                if tool:
                    self._checkKnownTool(tool, tool_impl)
                    tools.append( tool )

                    if not isinstance(tool_impl[ tool ], base):
                        self._errorExit('Tool {0} does not suite {1} type'.format(tool, item))
                        
            # Make sure tools defined in entryPoints are auto-detected
            #--
            for (ep, ed) in config.get('entryPoints', {}).items():
                tool = ed.get('tool', None)
                
                if tool:
                    self._checkKnownTool(tool, tool_impl)
                    tools.append( tool )

                    if not isinstance(tool_impl[ tool ], RuntimeTool):
                        self._errorExit('Tool {0} does not suite RuntimeTool type'.format(tool))

        # add all deps
        #--
        dep_generations = [ set(tools) ]
        tools = set( tools )
        postdeps = set()
        dep_length = 0
        last_index = 0
        while len( dep_generations ) != dep_length :
            dep_length = len( dep_generations )
            curr_index = last_index
            last_index = len(dep_generations)

            for g in dep_generations[curr_index:]:
                for tn in g:
                    self._checkKnownTool(tn, tool_impl)
                    t = tool_impl[tn]
                    moredeps = set(t.getDeps())
                    if moredeps:
                        dep_generations.append( moredeps )
                        tools.update( moredeps )
                    postdeps.update( set(t.getPostDeps()) - tools )

            if len( dep_generations ) == dep_length and postdeps:
                dep_generations.append( postdeps )
                tools.update( postdeps )
                postdeps = set()
    
        #---
        dep_generations.reverse()
        tools = []
        for d in dep_generations :
            tools.extend( d - set(tools) )
        config['toolOrder'] = tools
        
        #--
        for tool in tools :
            t = tool_impl[tool]
            t.envDeps( env )

        #--
        if config['toolTest']:
            for tool in tools :
                t = tool_impl[tool]
                t.sanitizeVersion( env )
                t.importEnv( env )
                if not t.isInstalled( env ):
                    break
        else :
            # note, it may have some undesired effect on parallel execution,
            # but let's leave that for now
            self._globalLock()
            
            for tool in tools :
                t = tool_impl[tool]
                t.sanitizeVersion( env )
                t.requireInstalled( env )
                if tool != curr_tool:
                    t.loadConfig( config )
                    
            self._globalUnlock()

        # Solves generic issues of ordering independent tools in
        # later execution with predictable results:
        # 1. sort by integer order
        # 2. sort by tool name
        tools.sort( key=lambda v: ( tool_impl[v].getOrder(), v ) )
