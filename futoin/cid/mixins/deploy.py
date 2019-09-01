#
# Copyright 2015-2019 Andrey Galkin <andrey@futoin.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from .data import DataSlots


class DeployMixIn(DataSlots):
    __slots__ = ()

    __VCS_CACHE_DIR = 'vcs'

    def __init__(self):
        super(DeployMixIn, self).__init__()
        self._current_dir = None
        self._devserve_mode = False

    def _redeployExit(self, deploy_type):
        self._warn(deploy_type + " has been already deployed. Use --redeploy.")
        self._sys.exit(0)

    def _rms_deploy(self, rms_pool, package=None):
        self._requireDeployLock()

        ospath = self._ospath
        os = self._os
        config = self._config
        rmstool = self._getRmsTool()

        # Find out package to deploy
        self._info('Finding package in RMS')
        package_list = rmstool.rmsGetList(config, rms_pool, package)

        if package:
            package_list = self._ext.fnmatch.filter(package_list, package)

        if not package_list:
            self._errorExit("No package found")

        package = self._versionutil.latest(package_list)
        package_basename = ospath.basename(package)
        self._info('Found package {0}'.format(package_basename))

        # cleanup first, in case of incomplete actions
        self._info('Pre-cleanup of deploy directory')
        self._deployCleanup([package_basename])

        # Prepare package name components
        (package_noext, package_ext) = ospath.splitext(package_basename)

        # Check if already deployed:
        if ospath.exists(package_noext):
            if config['reDeploy']:
                self._warn('Forcing re-deploy of the package')
            else:
                self._redeployExit('Package')

        # Retrieve package, if not available
        if not ospath.exists(package_basename):
            self._info('Retrieving the package')
            package_list = [package]
            package_list = rmstool.rmsProcessChecksums(
                config, rms_pool, package_list)
            rmstool.rmsRetrieve(config, rms_pool, package_list)

        package_noext_tmp = package_noext + '.tmp'

        # Prepare temporary folder
        os.mkdir(package_noext_tmp)

        # Unpack package to temporary folder
        self._info('Extracting the package')
        env = config['env']

        pkg_tool, compress_flag, _ = self._getTarTool(package_ext=package_ext)

        tool_args = [
            'x{0}f'.format(compress_flag),
            package_basename,
            '--strip-components=1',
            '-C', package_noext_tmp]

        pkg_tool.onExec(env, tool_args, False)

        # Common processing
        self._deployCommon(package_noext_tmp, package_noext,
                           [package_basename])

    def _vcsref_deploy(self, vcs_ref):
        self._requireDeployLock()

        ospath = self._ospath
        os = self._os
        config = self._config
        vcstool = self._getVcsTool()

        # Find out package to deploy
        self._info('Getting the latest revision of {0}'.format(vcs_ref))
        vcs_cache = ospath.realpath(self.__VCS_CACHE_DIR)
        rev = vcstool.vcsGetRefRevision(config, vcs_cache, vcs_ref)

        if not rev:
            self._errorExit("No VCS refs found")

        target_dir = vcs_ref.replace(os.sep, '_').replace(':', '_')
        target_dir += '__' + rev

        # cleanup first, in case of incomplete actions
        self._info('Pre-cleanup of deploy directory')
        self._deployCleanup([self.__VCS_CACHE_DIR, target_dir])

        # Check if already deployed:
        if ospath.exists(target_dir):
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
        vcstool.vcsExport(config, vcs_cache, vcs_ref, target_tmp)

        # Common processing
        self._deployCommon(target_tmp, target_dir, [self.__VCS_CACHE_DIR])

    def _vcstag_deploy(self, vcs_ref):
        self._requireDeployLock()

        ospath = self._ospath
        os = self._os
        config = self._config
        vcstool = self._getVcsTool()

        # Find out package to deploy
        self._info('Finding tag in VCS')
        vcs_cache = ospath.realpath(self.__VCS_CACHE_DIR)
        tag_list = vcstool.vcsListTags(config, vcs_cache, vcs_ref)

        if vcs_ref:
            tag_list = self._ext.fnmatch.filter(tag_list, vcs_ref)

        if not tag_list:
            self._errorExit("No tags found")

        vcs_ref = self._versionutil.latest(tag_list)
        target_dir = vcs_ref.replace(os.sep, '_').replace(':', '_')
        self._info('Found tag {0}'.format(vcs_ref))

        # cleanup first, in case of incomplete actions
        self._info('Pre-cleanup of deploy directory')
        self._deployCleanup([self.__VCS_CACHE_DIR, target_dir])

        # Check if already deployed:
        if ospath.exists(target_dir):
            if config['reDeploy']:
                self._warn('Forcing re-deploy of the VCS tag')
            else:
                self._redeployExit('VCS tag')

        # Retrieve tag
        self._info('Retrieving the VCS tag')
        vcs_ref_tmp = target_dir + '.tmp'
        vcstool.vcsExport(config, vcs_cache, vcs_ref, vcs_ref_tmp)

        # Common processing
        self._deployCommon(vcs_ref_tmp, target_dir, [self.__VCS_CACHE_DIR])

    def _deploy_setup(self):
        self._deployConfig()

    def _deployCommon(self, tmp, dst, cleanup_whitelist):
        self._requireDeployLock()

        ospath = self._ospath
        os = self._os
        stat = self._ext.stat

        self._current_dir = tmp
        config = self._config
        persistent_dir = ospath.realpath(
            config['env'].get('persistentDir', 'persistent'))

        # Predictable change of CWD
        self._overrides['wcDir'] = config['wcDir'] = ospath.realpath(tmp)
        self._processWcDir()
        config = self._config

        # Update tools
        if not self._detect.isDisabledToolsSetup(config['env']):
            self._info('Updating tools')
            self.tool_update(None)

        # Setup persistent folders
        self._info('Setting up read-write directories')

        if not ospath.exists(persistent_dir):
            os.makedirs(persistent_dir)

        wfile_wperm = stat.S_IRUSR | stat.S_IRGRP | stat.S_IWUSR | stat.S_IWGRP
        wdir_wperm = wfile_wperm | stat.S_IXUSR | stat.S_IXGRP

        for def_dir in config.get('persistent', []):
            persist_dst = ospath.join(persistent_dir, def_dir)
            sym_target = ospath.relpath(persist_dst, ospath.dirname(def_dir))
            self._info('{0} -> {1}'.format(def_dir, persist_dst),
                       'Making persistent: ')

            if ospath.isdir(def_dir):
                self._info('copy tree', ' >> ')
                self._ext.dir_util.copy_tree(
                    def_dir, persist_dst,
                    preserve_symlinks=1, preserve_mode=0
                )
                self._pathutil.rmTree(def_dir)
                os.symlink(sym_target, def_dir)
                self._pathutil.chmodTree(
                    persist_dst, wdir_wperm, wfile_wperm, False)
            elif ospath.isfile(def_dir):
                self._info('moving file', ' >> ')
                self._ext.shutil.move(def_dir, persist_dst)
                os.unlink(def_dir)
                os.symlink(sym_target, def_dir)
                os.chmod(persist_dst, wfile_wperm)
            elif ospath.isdir(persist_dst):
                self._info('symlink existing dir', ' >> ')
                os.symlink(sym_target, def_dir)
                self._pathutil.chmodTree(
                    persist_dst, wdir_wperm, wfile_wperm, False)
            else:
                self._info('create & symlink dir', ' >> ')
                os.makedirs(persist_dst, wdir_wperm)
                os.symlink(sym_target, def_dir)

        # Build
        if config.get('deployBuild', False):
            self._info('Building project in deployment')
            self.prepare(None)
            self.build()

        # Symlink .env file, if exists in deploy folder
        if ospath.exists('../.env'):
            os.symlink('../.env', '.env')

        # Complete migration
        self.migrate()

        # return back
        self._processDeployDir()
        config = self._config

        # Setup read-only permissions
        self._info('Setting up read-only permissions')

        file_perm = stat.S_IRUSR | stat.S_IRGRP
        dir_perm = file_perm | stat.S_IXUSR | stat.S_IXGRP
        self._pathutil.chmodTree(tmp, dir_perm, file_perm, True)

        for wdir in config.get('writable', []):
            wdir = ospath.join(tmp, wdir)
            self._pathutil.chmodTree(wdir, wdir_wperm, wfile_wperm, True)

        # Setup services
        self._deployConfig()

        # Move in place
        self._info('Switching current deployment')
        if ospath.exists(dst):
            # re-deploy case
            os.chmod(dst, stat.S_IRWXU)  # macOS
            os.rename(dst, dst + '.tmprm')

        os.chmod(tmp, stat.S_IRWXU)  # macOS
        os.rename(tmp, dst)
        os.chmod(dst, dir_perm)

        os.symlink(dst, 'current.tmp')
        os.rename('current.tmp', 'current')
        self._current_dir = None

        # Re-run
        self._reloadServices()

        # Cleanup old packages and deploy dirs
        self._info('Post-cleanup of deploy directory')
        self._deployCleanup(cleanup_whitelist)

    def _deployCleanup(self, whitelist):
        self._requireDeployLock()

        ospath = self._ospath
        os = self._os

        if ospath.exists('current'):
            whitelist.append(ospath.basename(os.readlink('current')))

        whitelist += [
            'current',
            'persistent',
            self._FUTOIN_JSON,
        ]

        for f in os.listdir('.'):
            (f_noext, f_ext) = ospath.splitext(f)

            if f[0] == '.' or f in whitelist:
                continue

            self._pathutil.rmTree(f)

    def _deployConfig(self):
        self._requireDeployLock()

        self._rebalanceServices()
        self._configServices()

        self._writeDeployConfig()

    def _writeDeployConfig(self):
        self._requireDeployLock()

        config = self._config
        orig_config = self._deploy_config
        new_config = self._exportConfig(orig_config)

        if config.get('rms', None):
            new_config['rms'] = config['rms']
            new_config['rmsRepo'] = config.get('rmsRepo', '')

        if config.get('vcs', None):
            new_config['vcs'] = config['vcs']
            new_config['vcsRepo'] = config.get('vcsRepo', '')

        new_config['deploy'] = config.get('deploy', {})
        new_config['env'] = orig_config.get('env', {})

        self._info('Writing deployment config in {0}'.format(
            self._os.getcwd()))
        self._pathutil.writeJSONConfig(self._FUTOIN_JSON, new_config)

        merged_config = self._exportConfig(config)
        merged_config['deploy'] = new_config['deploy']
        merged_config['env'] = config['env']

        self._pathutil.writeJSONConfig(self._FUTOIN_MERGED_JSON, merged_config)

    def _reloadServices(self):
        self._requireDeployLock()

        # Only service master mode is supported this way
        # Otherwise, deployment invoker is responsible for service reload.
        self._reloadServiceMaster()

    def _rebalanceServices(self):
        self._info('Re-balancing services')
        from ..details.resourcealgo import ResourceAlgo
        ResourceAlgo().configServices(self._config)

    def _configServices(self):
        self._info('Configuring services')
        self._requireDeployLock()

        config = self._config
        service_list = self._configServiceList(config)

        if not service_list:
            return

        deploy = config['deploy']
        runtimeDir = deploy['runtimeDir']
        tmpDir = deploy['tmpDir']

        pathutil = self._pathutil

        # DO NOT use realpath as it may point to "old current"
        config['wcDir'] = pathutil.safeJoin(config['deployDir'], 'current')

        pathutil.mkDir(runtimeDir)
        pathutil.mkDir(tmpDir)

        auto_services = config['deploy']['autoServices']

        from ..runtimetool import RuntimeTool

        for svc in service_list:
            tool = svc['tool']
            t = self._getTool(tool)

            if isinstance(t, RuntimeTool):
                cfg_svc = auto_services[svc['name']][svc['instanceId']]
                t.onPreConfigure(config, runtimeDir, svc, cfg_svc)
            else:
                self._errorExit(
                    'Tool "{0}" for "{1}" is not of RuntimeTool type'
                    .format(tool, svc['name']))

    def _processDeployDir(self):
        os = self._os
        ospath = self._ospath
        stat = self._ext.stat

        os.umask(0o027)

        deploy_dir = self._overrides['deployDir']

        # make sure wcDir is always set to current
        current = self._getDeployCurrent()
        wc_dir = ospath.join(deploy_dir, current)
        self._overrides['wcDir'] = wc_dir

        if not deploy_dir:
            deploy_dir = ospath.realpath('.')
            self._overrides['deployDir'] = deploy_dir

        self._info('Using {0} as deploy directory'.format(deploy_dir))

        if not ospath.exists(deploy_dir):
            self._info('Creating deploy directory')
            os.makedirs(deploy_dir)
            self._deployLock()
            self._deployUnlock()
        else:
            self._checkDeployLock()

        st_mode = os.stat(deploy_dir).st_mode

        if not st_mode & st_mode:
            os.chmod(deploy_dir, st_mode | st_mode)

        if self._config is not None:
            self._info('Re-initializing config')

        self._initConfig()

        if deploy_dir != os.getcwd():
            self._infoLabel('Changing to: ', deploy_dir)
            os.chdir(deploy_dir)

        # some tools may benefit of it
        if not self._devserve_mode:
            self._environ['CID_DEPLOY_HOME'] = deploy_dir

        deploy = self._config['deploy']

        if 'user' not in deploy:
            deploy['user'] = self._ext.pwd.getpwuid(os.geteuid())[0]

        if 'group' not in deploy:
            deploy['group'] = self._ext.grp.getgrgid(os.getegid())[0]

    def _deploy_set_action(self, name, actions):
        dc = self._deploy_config
        dc_actions = dc.setdefault('actions', {})
        dc_actions[name] = actions

    def _deploy_reset_action(self):
        dc = self._deploy_config
        dc['actions'] = {}

    def _deploy_set_persistent(self, paths):
        dc = self._deploy_config
        persistent = set(dc.get('persistent', []))
        persistent.update(set(paths))
        dc['persistent'] = sorted(list(persistent))

    def _deploy_reset_persistent(self):
        dc = self._deploy_config
        dc['persistent'] = []

    def _deploy_set_writable(self, paths):
        dc = self._deploy_config
        writable = set(dc.get('writable', []))
        writable.update(set(paths))
        dc['writable'] = sorted(list(writable))

    def _deploy_reset_writable(self):
        dc = self._deploy_config
        dc['writable'] = []

    def _deploy_set_entrypoint(self, name, tool, path, tune):
        dc = self._deploy_config
        epoints = dc.setdefault('entryPoints', {})
        ep = epoints.setdefault(name, {})
        ep['tool'] = tool
        ep['path'] = path
        ep['tune'] = self._deploy_set_tune_common(ep.get('tune', {}), tune)

    def _deploy_reset_entrypoint(self):
        dc = self._deploy_config
        dc['entryPoints'] = {}

    def _deploy_set_tune_common(self, target, tune):
        if len(tune) == 1 and len(tune[0]) and tune[0][0] == '{':
            return self._configutil.parseJSON(tune[0])
        else:
            for t in tune:
                t = t.split('=', 1)
                tkey = t[0]

                if len(t) == 2 and t[1]:
                    target[tkey] = t[1]
                elif tkey in target:
                    del target[tkey]
            return target

    def _deploy_set_env(self, var, val):
        dc = self._deploy_config
        env = dc.setdefault('env', {})

        if val is not None:
            env[var] = val
        elif var in env:
            del env[var]

    def _deploy_reset_env(self):
        dc = self._deploy_config
        dc['env'] = {}

    def _deploy_set_webcfg(self, var, val):
        dc = self._deploy_config
        webcfg = dc.setdefault('webcfg', {})

        if var == 'mounts':
            mounts = webcfg.setdefault('mounts', {})
            val = val.split('=', 1)
            var = val[0]

            if len(val) == 2 and val[1]:
                mounts[var] = val[1]
            elif var in mounts:
                del mounts[var]

        elif val is not None:
            webcfg[var] = val

        elif var in webcfg:
            del webcfg[var]

    def _deploy_reset_webcfg(self):
        dc = self._deploy_config
        dc['webcfg'] = {}

    def _deploy_set_webmount(self, path, json):
        dc = self._deploy_config
        webcfg = dc.setdefault('webcfg', {})

        mounts = webcfg.setdefault('mounts', {})

        if json is None:
            del mounts[path]
        else:
            mounts[path] = self._configutil.parseJSON(json)

    def _deploy_reset_webmount(self):
        dc = self._deploy_config
        webcfg = dc.setdefault('webcfg', {})

        webcfg['mounts'] = {}

    def _deploy_set_tools(self, tools):
        dc = self._deploy_config

        # set fresh
        dc_tools = {}
        dc['tools'] = dc_tools

        for t in tools:
            v = (t + '=*').split('=')
            v = list(filter(None, v))
            dc_tools[v[0]] = v[1]

    def _deploy_reset_tools(self):
        dc = self._deploy_config
        dc['tools'] = {}

    def _deploy_set_tooltune(self, tool, tune):
        dc = self._deploy_config
        toolTune = dc.setdefault('toolTune', {})
        toolTune[tool] = self._deploy_set_tune_common(
            toolTune.get(tool, {}), tune)

    def _deploy_reset_tooltune(self):
        dc = self._deploy_config
        dc['toolTune'] = {}

    def _getDeployCurrent(self):
        return self._current_dir or 'current'
