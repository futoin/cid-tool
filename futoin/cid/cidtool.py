
from __future__ import print_function, absolute_import

import os
import sys
import subprocess
import shlex
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
import signal
import copy
import errno
from collections import OrderedDict
from distutils import dir_util

from .mixins.path import PathMixIn
from .mixins.util import UtilMixIn
from .mixins.package import PackageMixIn
from .coloring import Coloring

from .vcstool import VcsTool
from .rmstool import RmsTool
from .buildtool import BuildTool
from .testtool import TestTool
from .migrationtool import MigrationTool
from .runtimetool import RuntimeTool


__all__ = ['CIDTool']
ospath = os.path


def _call_cmd(cmd):
    print(Coloring.infoLabel('Call: ') +
          Coloring.info(subprocess.list2cmdline(cmd)),
          file=sys.stderr)

    subprocess.check_call(cmd, stdin=subprocess.PIPE)


def _call_actions(name, actions, args):
    act = actions[name]

    if not isinstance(act, list):
        act = [act]

    for cmd in act:
        if cmd.startswith('@cid'):
            cmd = shlex.split(cmd)
            _call_cmd([sys.executable, '-mfutoin.cid'] + cmd[1:] + args)
        elif cmd in actions:
            _call_actions(cmd, actions, args)
        else:
            if args:
                cmd = '{0} {1}'.format(cmd, subprocess.list2cmdline(args))
            _call_cmd(['sh', '-c', cmd])


def cid_action(f):
    def custom_f(self, *args, **kwargs):
        config = self._config

        try:
            fn = f.func_name
        except AttributeError:
            fn = f.__name__

        actions = config.get('actions', {})

        if fn in actions:
            for act in actions[fn]:
                if not isinstance(act, list):
                    act = [act]

                for cmd in act:
                    if cmd == '<default>' or cmd == '@default':
                        f(self, *args, **kwargs)
                    elif cmd.startswith('@cid'):
                        cmd = shlex.split(cmd)
                        _call_cmd([sys.executable, '-mfutoin.cid'] + cmd[1:])
                    elif cmd in actions:
                        filt_args = list(filter(None, args))
                        _call_actions(cmd, actions, filt_args)
                    else:
                        _call_cmd(['sh', '-c', cmd])
        else:
            f(self, *args, **kwargs)
    return custom_f


class TimeoutException(RuntimeError):
    @classmethod
    def alarmHandler(cls, *args, **kwargs):
        raise TimeoutException('Alarm')

#=============================================================================


class HelpersMixIn(object):
    def _checkKnownTool(self, tool, tool_impl=None):
        if tool_impl is None:
            tool_impl = self._tool_impl

        if tool not in tool_impl:
            self._errorExit(
                'Implementation for "{0}" was not found'.format(tool))

    def _forEachTool(self, cb, allow_failure=False, base=None):
        config = self._config
        tool_impl = self._tool_impl
        tools = config['toolOrder']

        for t in tools:
            t = tool_impl[t]

            if base and not isinstance(t, base):
                continue

            try:
                cb(config, t)
            except RuntimeError as e:
                if not allow_failure:
                    raise e

    def _getVcsTool(self):
        config = self._config
        vcs = config.get('vcs', None)

        if not vcs:
            self._errorExit(
                'Unknown VCS. Please set through --vcsRepo or project manifest')

        vcstool = self._tool_impl[vcs]

        if not config.get('vcsRepo', None):  # also check it set
            try:
                config['vcsRepo'] = vcstool.vcsGetRepo(config)
            except subprocess.CalledProcessError as e:
                pass

            if not config.get('vcsRepo', None):
                self._errorExit(
                    'Unknown VCS repo. Please set through --vcsRepo or project manifest')

        # Make sure these are present event after config is re-read
        self._overrides['vcs'] = vcs
        self._overrides['vcsRepo'] = config['vcsRepo']

        return vcstool

    def _getRmsTool(self):
        config = self._config
        rms = config.get('rms', None)

        if not rms:
            self._errorExit(
                'Unknown RMS. Please set through --rmsRepo or project manifest')

        if not config.get('rmsRepo', None):  # also check it set
            self._errorExit(
                'Unknown RMS repo. Please set through --rmsRepo or project manifest')

        # Make sure these are present event after config is re-read
        self._overrides['rms'] = rms
        self._overrides['rmsRepo'] = config['rmsRepo']

        return self._tool_impl[rms]

    def _getTarTool(self, compressor=None):
        env = self._config['env']

        tar_tool = self._tool_impl['tar']
        tar_tool.requireInstalled(env)

        if compressor:
            self._tool_impl[compressor].requireInstalled(env)

        return tar_tool

    def _processWcDir(self):
        config = self._config
        wcDir = config['wcDir']

        if not ospath.exists(wcDir):
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

            print(Coloring.infoLabel('Changing to: ') + Coloring.info(wcDir),
                  file=sys.stderr)
            os.chdir(wcDir)
            self._overrides['wcDir'] = config['wcDir'] = os.getcwd()
            self._initConfig()


#=============================================================================
class LockMixIn(object):
    DEPLOY_LOCK_FILE = '.futoin-deploy.lock'
    MASTER_LOCK_FILE = '.futoin-master.lock'
    GLOBAL_LOCK_FILE = ospath.join(os.environ['HOME'], '.futoin-global.lock')

    def _initLocks(self):
        self._deploy_lock = None
        self._master_lock = None
        self._global_lock = None

    def _lockCommon(self, lock, file, flags):
        assert self.__dict__[lock] is None
        self.__dict__[lock] = os.open(file, os.O_WRONLY | os.O_CREAT)
        try:
            fcntl.flock(self.__dict__[lock], flags)
        except Exception as e:
            self._errorExit('FAILED to acquire{0}: {1}'.format(
                lock.replace('_', ' '), e))

    def _unlockCommon(self, lock):
        fcntl.flock(self.__dict__[lock], fcntl.LOCK_UN)
        os.close(self.__dict__[lock])
        self.__dict__[lock] = None

    def _deployLock(self):
        self._lockCommon(
            '_deploy_lock',
            ospath.join(self._config['deployDir'], self.DEPLOY_LOCK_FILE),
            fcntl.LOCK_EX | fcntl.LOCK_NB
        )

    def _deployUnlock(self):
        self._unlockCommon('_deploy_lock')

    def _requireDeployLock(self):
        if self._deploy_lock is None:
            self._errorExit('Deploy lock must be already acquired')

    def _globalLock(self):
        self._lockCommon('_global_lock', self.GLOBAL_LOCK_FILE, fcntl.LOCK_EX)

    def _globalUnlock(self):
        self._unlockCommon('_global_lock')

    def _masterLock(self):
        self._lockCommon(
            '_master_lock',
            ospath.join(self._config['deployDir'], self.MASTER_LOCK_FILE),
            fcntl.LOCK_EX | fcntl.LOCK_NB
        )

    def _masterUnlock(self):
        self._unlockCommon('_master_lock')


#=============================================================================
class ConfigMixIn(object):
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
        ('pluginPacks', list),
    ])

    CONFIG_TUNE_VARS = OrderedDict([
        ('minMemory', 'memory'),
        ('maxMemory', 'memory'),
        ('maxTotalMemory', 'memory'),
        ('connMemory', 'memory'),
        ('connFD', int),
        ('debugOverhead', 'memory'),
        ('debugConnOverhead', 'memory'),
        ('scalable', bool),
        ('reloadable', bool),
        ('multiCore', bool),
        ('exitTimeoutMS', int),
        ('cpuWeight', 'weight'),
        ('memWeight', 'weight'),
        ('instances', int),
        ('maxInstances', int),
        ('socketTypes', list),
        ('socketProtocols', list),
        ('maxRequestSize', 'memory'),
    ])

    FUTOIN_ENV_VARS = OrderedDict([
        ('type', _str_type),
        ('persistentDir', _str_type),
        ('vars', dict),
        ('plugins', dict),
        ('pluginPacks', list),
        ('externalSetup', bool),
    ])

    def _initConfig(self):
        errors = []

        #--
        user_home = os.environ.get('HOME', '/')
        user_config_path = ospath.join(user_home, '.' + self._FUTOIN_JSON)

        if not ospath.exists(user_config_path) and user_home != self._overrides['wcDir']:
            user_config_path = ospath.join(user_home, self._FUTOIN_JSON)

        user_config_path = ospath.realpath(user_config_path)

        global_config_file = ospath.join(
            '/', 'etc', 'futoin', self._FUTOIN_JSON)
        global_config_file = ospath.realpath(global_config_file)

        deploy_config_file = None
        deploy_dir = self._overrides.get('deployDir', None)

        if deploy_dir:
            current = self._getDeployCurrent()
            deploy_config_file = ospath.join(deploy_dir, self._FUTOIN_JSON)
            deploy_config_file = ospath.realpath(deploy_config_file)
            project_config_file = ospath.join(
                deploy_dir, current, self._FUTOIN_JSON)
            project_config_file = ospath.realpath(project_config_file)
        else:
            project_config_file = ospath.realpath(self._FUTOIN_JSON)

        #--
        gc = {'env': {}}
        uc = {'env': {}}
        dc = {}
        pc = {}

        gc = self._loadJSONConfig(global_config_file, gc)

        if user_config_path not in (deploy_config_file, project_config_file):
            uc = self._loadJSONConfig(user_config_path, uc)

        if project_config_file != deploy_config_file:
            pc = self._loadJSONConfig(project_config_file, pc)

        if deploy_config_file:
            dc = self._loadJSONConfig(deploy_config_file, dc)

        #---
        self._global_config = gc
        self._user_config = uc
        self._deploy_config = dc
        self._project_config = pc
        #--

        config = dict(pc)

        # Deployment config can override project config
        for (k, v) in dc.items():
            if k in ('deploy', 'env'):
                continue
            elif k == 'entryPoints':
                config_epoints = config.setdefault('entryPoints', {})

                for (ek, ev) in v.items():
                    cep = config_epoints.setdefault(ek, {})

                    if ek == 'tune':
                        cep_tune = cep.setdefault('tune', {})
                        cep_tune.update(ev)
                    else:
                        cep[ek] = ev
            elif k == 'actions':
                config_actions = config.setdefault('actions', {})

                for (ak, av) in v.items():
                    if ak in config_actions:
                        if not isinstance(av, list):
                            lav = [av]
                        else:
                            lav = list(av)

                        try:
                            try:
                                pos = lav.index('@default')
                            except ValueError:
                                pos = lav.index('<default>')

                            cv = config_actions[ak]

                            if not isinstance(cv, list):
                                cv = [cv]

                            lav[pos:pos + 1] = cv
                            av = lav
                        except ValueError:
                            pass

                    config_actions[ak] = av
            elif k == 'persistent':
                persistent = set(config.get('persistent', []))
                persistent.update(set(v))
                config['persistent'] = list(persistent)
            else:
                config[k] = v

        self._sanitizeConfig(config, errors)

        if 'env' in pc:
            errors.append('.env node must not be set in project config')

        if 'deploy' in pc:
            errors.append('.deploy node must not be set in project config')

        env = dict(dc.get('env', {}))

        for ct in (uc, gc):
            if 'env' not in ct or len(ct) != 1:
                errors.append(
                    'User and Global configs must have the only .env node')
                continue

            for (k, v) in ct['env'].items():
                if k == 'plugins':
                    plugins = env.setdefault('plugins', {})

                    for pk, pv in env['plugins'].items():
                        plugins.setdefault(pk, pv)
                elif k == 'pluginPacks':
                    pluginPacks = env.setdefault('pluginPacks', [])
                    pluginPacks += v
                else:
                    env.setdefault(k, v)

        self._initEnv(env)

        config['env'] = env
        config.update(self._overrides)
        self._config = config

        self._initTools()

        #
        entry_points = config.get('entryPoints', {})

        for (en, ep) in entry_points.items():
            t = self._tool_impl[ep['tool']]
            ep_tune = ep.setdefault('tune', {})

            for (tk, tv) in t.tuneDefaults().items():
                ep_tune.setdefault(tk, tv)

        # run again to check tuneDefaults() from plugins
        self._sanitizeEntryPoints(entry_points, errors)

        #---
        deploy = dc.get('deploy', {})
        config['deploy'] = deploy

        if '_deploy' in config:
            _deploy = config['_deploy']
            del config['_deploy']

            for (dk, dv) in _deploy.items():
                if dv is None:
                    pass
                elif dv == 'auto':
                    try:
                        del deploy[dk]
                    except KeyError:
                        pass
                else:
                    deploy[dk] = dv

        self._sanitizeDeployConfig(config, errors)

        #---
        if errors:
            self._errorExit(
                "Configuration issues are found:\n\n* " +
                "\n* ".join(set(errors)))

    def _getDeployCurrent(self):
        return self._current_dir or 'current'

    def _sanitizeConfig(self, config, errors):
        conf_vars = self.CONFIG_VARS

        for (k, v) in config.items():
            if k not in conf_vars:
                self._warn('Removing unknown config variable "{0}"'.format(k))
                del config[k]
            elif not isinstance(v, conf_vars[k]):
                req_t = conf_vars[k]
                if isinstance(req_t, tuple):
                    req_t = req_t[0]

                errors.append(
                    'Config variable "{0}" type "{1}" is not instance of "{2}"'
                    .format(k, v.__class__.__name__, req_t[0].__name__)
                )

        #---
        # Make sure futoinTool is enabled, if futoin.json is present.
        # Otherwise, auto-detection gets disabled and futoin.json is not
        # updated
        tools = config.get('tools', None)

        if tools and 'futoin' not in tools:
            tools['futoin'] = True

        #---
        entry_points = config.get('entryPoints', None)

        if entry_points:
            self._sanitizeEntryPoints(entry_points, errors)

        #---
        toolTune = config.get('toolTune', None)

        if toolTune:
            for (tn, tune) in toolTune.items():
                if not isinstance(tune, dict):
                    errors.append(
                        'Tool tune "{0}" is not of map type'.format(tn))

    def _sanitizeEntryPoints(self, entry_points, errors):
        for (en, ep) in entry_points.items():
            for k in ['tool', 'path']:
                if k not in ep:
                    errors.append(
                        'Entry point "{0}" is missing "{1}"'.format(en, k))

            if 'tune' in ep:
                ep_tune = ep['tune']

                if not isinstance(ep_tune, dict):
                    errors.append(
                        'Entry point "{0}" has invalid tune parameter'.format(en))
                    continue

                for (tk, tt) in self.CONFIG_TUNE_VARS.items():
                    try:
                        tv = ep_tune[tk]
                    except KeyError:
                        continue

                    if tt == 'memory':
                        self._sanitizeMemory(
                            "{0}/{1}".format(en, tk), tv, errors)

                    elif tt == 'weight':
                        if not isinstance(tv, int) or tv <= 0:
                            errors.append(
                                'Weight value "{0}/{1}" must be positive'.format(en, tk))

                    elif not isinstance(tv, tt):
                        errors.append(
                            'Config tune variable "{0}" type "{1}" is not instance of "{2}"'
                            .format(tk, tv.__class__.__name__, tt.__name__)
                        )

    def _sanitizeDeployConfig(self, dc, errors):
        deploy = dc.get('deploy', {})

        if 'maxTotalMemory' in deploy:
            maxTotalMemory = deploy['maxTotalMemory']

            self._sanitizeMemory('deploy/maxTotalMemory',
                                 maxTotalMemory, errors)

        if 'maxCpuCount' in deploy:
            val = deploy['maxCpuCount']

            if not isinstance(val, int) or val <= 0:
                errors.append(
                    '"deploy/maxCpuCount" must be a positive integer')

    def _sanitizeMemory(self, key, val, errors):
        try:
            self._parseMemory(val)
        except:
            errors.append(
                'Memory value "{0}" must be positive '
                'integer with B, K, M or G postfix (e.g. "16M")'
                .format(key))

    def _initEnv(self, env):
        env.setdefault('type', 'prod')
        env.setdefault('vars', {})
        env.setdefault('plugins', {})
        env.setdefault('pluginPacks', [])
        env.setdefault('externalSetup', False)

        timeouts = env.setdefault('timeouts', {})
        timeouts.setdefault('connect', 10)
        read_to = timeouts.setdefault('read', 60)
        timeouts.setdefault('total', read_to * 60)

        env.setdefault('binDir', ospath.join(os.environ['HOME'], 'bin'))
        self._addBinPath(env['binDir'])

        #---
        env_vars = self.FUTOIN_ENV_VARS

        for (k, v) in env.items():
            if k not in env_vars:
                continue
            elif not isinstance(v, env_vars[k]):
                req_t = env_vars[k]
                if isinstance(req_t, tuple):
                    req_t = req_t[0]

                self._errorExit(
                    'Config variable "{0}" type "{1}" is not instance of "{2}"'
                    .format(k, v.__class__.__name__, req_t[0].__name__)
                )

        if env['type'] not in ('prod', 'test', 'dev'):
            self._errorExit(
                'Not valid environment type "{0}'.format(env['type']))

    def _initTools(self):
        config = self._config
        env = config['env']

        #---
        config['projectRootSet'] = set(os.listdir('.'))

        #---
        plugins = {}
        plugins.update(env['plugins'])
        plugins.update(config.get('plugins', {}))

        plugin_packs = []
        plugin_packs += env['pluginPacks']
        plugin_packs += config.get('pluginPacks', {})
        plugin_packs.append('futoin.cid.tool')

        for pack_mod_name in plugin_packs:
            m = importlib.import_module(pack_mod_name)
            pack_dir = ospath.dirname(m.__file__)
            tool_files = os.listdir(pack_dir)
            tool_files = fnmatch.filter(tool_files, '*tool.py')

            for f in tool_files:
                tool = f.replace('tool.py', '')
                tool_mod_name = '{0}.{1}tool'.format(pack_mod_name, tool)
                plugins[tool] = tool_mod_name

        tool_impl = {}
        self._tool_impl = tool_impl

        for (tool, tool_mod_name) in plugins.items():
            if tool not in tool_impl:
                tool_module = importlib.import_module(tool_mod_name)
                tool_impl[tool] = getattr(tool_module, tool + 'Tool')(tool)

        #---
        curr_tool = config.get('tool', None)

        if curr_tool:
            tools = [curr_tool]
            tool_ver = config.get('toolVer', None)

            if tool_ver:
                config['env'][curr_tool + 'Ver'] = tool_ver
        else:
            config_tools = config.get('tools', {})
            tools = []

            if config_tools:
                if not isinstance(config_tools, dict):
                    self._errorExit(
                        'futoin.json:tools must be a map of tool=>version pairs')

                for (tool, v) in config_tools.items():
                    self._checkKnownTool(tool, tool_impl)
                    tools.append(tool)

                    if v != '*' and v != True:
                        env[tool + 'Ver'] = v
            else:
                for (n, t) in tool_impl.items():
                    if t.autoDetect(config):
                        tools.append(n)

            # Make sure deps & env are processed for cli-supplied tools
            #--
            for (item, base) in {'rms': RmsTool, 'vcs': VcsTool}.items():
                tool = config.get(item, None)

                if tool:
                    self._checkKnownTool(tool, tool_impl)
                    tools.append(tool)

                    if not isinstance(tool_impl[tool], base):
                        self._errorExit(
                            'Tool {0} does not suite {1} type'.format(tool, item))

            # Make sure tools defined in entryPoints are auto-detected
            #--
            for (ep, ed) in config.get('entryPoints', {}).items():
                tool = ed.get('tool', None)

                if tool:
                    self._checkKnownTool(tool, tool_impl)
                    tools.append(tool)

                    if not isinstance(tool_impl[tool], RuntimeTool):
                        self._errorExit(
                            'Tool {0} does not suite RuntimeTool type'.format(tool))

        # add all deps
        #--
        dep_generations = [set(tools)]
        tools = set(tools)
        postdeps = set()
        dep_length = 0
        last_index = 0
        while len(dep_generations) != dep_length:
            dep_length = len(dep_generations)
            curr_index = last_index
            last_index = len(dep_generations)

            for g in dep_generations[curr_index:]:
                for tn in g:
                    self._checkKnownTool(tn, tool_impl)
                    t = tool_impl[tn]
                    moredeps = set(t.getDeps())
                    if moredeps:
                        dep_generations.append(moredeps)
                        tools.update(moredeps)
                    postdeps.update(set(t.getPostDeps()) - tools)

            if len(dep_generations) == dep_length and postdeps:
                dep_generations.append(postdeps)
                tools.update(postdeps)
                postdeps = set()

        #---
        if self._isMacOS() and tools:
            # Make sure Homebrew is always implicit first tool
            dep_generations.append(set(['brew']))

        #---
        dep_generations.reverse()
        tools = []
        for d in dep_generations:
            tools.extend(d - set(tools))
        config['toolOrder'] = tools

        #--
        for tool in tools:
            t = tool_impl[tool]
            t.envDeps(env)

        #--
        if config['toolTest']:
            for tool in tools:
                t = tool_impl[tool]
                t.sanitizeVersion(env)
                t.importEnv(env)
                if not t.isInstalled(env):
                    break
        else:
            # note, it may have some undesired effect on parallel execution,
            # but let's leave that for now
            self._globalLock()

            for tool in tools:
                t = tool_impl[tool]
                t.sanitizeVersion(env)
                t.requireInstalled(env)
                if tool != curr_tool:
                    t.loadConfig(config)

            self._globalUnlock()

        # Solves generic issues of ordering independent tools in
        # later execution with predictable results:
        # 1. sort by integer order
        # 2. sort by tool name
        tools.sort(key=lambda v: (tool_impl[v].getOrder(), v))


#=============================================================================
class DeployMixIn(object):
    VCS_CACHE_DIR = 'vcs'
    _devserve_mode = False

    def _redeployExit(self, deploy_type):
        self._warn(deploy_type + " has been already deployed. Use --redeploy.")
        sys.exit(0)

    def _rms_deploy(self, rms_pool, package=None):
        self._requireDeployLock()

        config = self._config
        rmstool = self._getRmsTool()

        # Find out package to deploy
        self._info('Finding package in RMS')
        package_list = rmstool.rmsGetList(config, rms_pool, package)

        if package:
            package_list = fnmatch.filter(package_list, package)

        if not package_list:
            self._errorExit("No package found")

        package = self._getLatest(package_list)
        self._info('Found package {0}'.format(package))

        # cleanup first, in case of incomplete actions
        self._info('Pre-cleanup of deploy directory')
        self._deployCleanup([package])

        # Prepare package name components
        package_basename = ospath.basename(package)
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

        if package_ext == '.txz':
            tar_tool = self._getTarTool('xz')
            tar_args = ['xJf', package_basename, '-C', package_noext_tmp]
            tar_tool.onExec(env, tar_args, False)
        elif package_ext == '.tbz2':
            tar_tool = self._getTarTool('bzip2')
            tar_args = ['xjf', package_basename, '-C', package_noext_tmp]
            tar_tool.onExec(env, tar_args, False)
        elif package_ext == '.tgz':
            tar_tool = self._getTarTool('gzip')
            tar_args = ['xzf', package_basename, '-C', package_noext_tmp]
            tar_tool.onExec(env, tar_args, False)
        elif package_ext == '.tar':
            tar_tool = self._getTarTool()
            tar_args = ['xf', package_basename, '-C', package_noext_tmp]
            tar_tool.onExec(env, tar_args, False)
        else:
            self._errorExit('Not supported package format: ' + package_ext)

        # Common processing
        self._deployCommon(package_noext_tmp, package_noext, [package])

    def _vcsref_deploy(self, vcs_ref):
        self._requireDeployLock()

        config = self._config
        vcstool = self._getVcsTool()

        # Find out package to deploy
        self._info('Getting the latest revision of {0}'.format(vcs_ref))
        vcs_cache = ospath.realpath(self.VCS_CACHE_DIR)
        rev = vcstool.vcsGetRefRevision(config, vcs_cache, vcs_ref)

        if not rev:
            self._errorExit("No VCS refs found")

        target_dir = vcs_ref.replace(os.sep, '_').replace(':', '_')
        target_dir += '__' + rev

        # cleanup first, in case of incomplete actions
        self._info('Pre-cleanup of deploy directory')
        self._deployCleanup([self.VCS_CACHE_DIR, target_dir])

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
        self._deployCommon(target_tmp, target_dir, [self.VCS_CACHE_DIR])

    def _vcstag_deploy(self, vcs_ref):
        self._requireDeployLock()

        config = self._config
        vcstool = self._getVcsTool()

        # Find out package to deploy
        self._info('Finding tag in VCS')
        vcs_cache = ospath.realpath(self.VCS_CACHE_DIR)
        tag_list = vcstool.vcsListTags(config, vcs_cache, vcs_ref)

        if vcs_ref:
            tag_list = fnmatch.filter(tag_list, vcs_ref)

        if not tag_list:
            self._errorExit("No tags found")

        vcs_ref = self._getLatest(tag_list)
        target_dir = vcs_ref.replace(os.sep, '_').replace(':', '_')
        self._info('Found tag {0}'.format(vcs_ref))

        # cleanup first, in case of incomplete actions
        self._info('Pre-cleanup of deploy directory')
        self._deployCleanup([self.VCS_CACHE_DIR, target_dir])

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
        self._deployCommon(vcs_ref_tmp, target_dir, [self.VCS_CACHE_DIR])

    def _deploy_setup(self):
        self._deployConfig()

    def _deployCommon(self, tmp, dst, cleanup_whitelist):
        self._requireDeployLock()

        self._current_dir = tmp
        config = self._config
        persistent_dir = ospath.realpath(
            config['env'].get('persistentDir', 'persistent'))

        # Predictable change of CWD
        self._overrides['wcDir'] = config['wcDir'] = ospath.realpath(tmp)
        self._processWcDir()
        config = self._config

        # Update tools
        if not self._isExternalToolsSetup(config['env']):
            self._info('Updating tools')
            self.tool_update(None)

        # Setup persistent folders
        self._info('Setting up read-write directories')

        if not ospath.exists(persistent_dir):
            os.makedirs(persistent_dir)

        wfile_wperm = stat.S_IRUSR | stat.S_IRGRP | stat.S_IWUSR | stat.S_IWGRP
        wdir_wperm = wfile_wperm | stat.S_IXUSR | stat.S_IXGRP

        for dd in config.get('persistent', []):
            pd = ospath.relpath(ospath.join(
                persistent_dir, dd), ospath.dirname(dd))
            self._info('{0} -> {1}'.format(dd, pd), 'Making persistent: ')

            if ospath.isdir(dd):
                dir_util.copy_tree(
                    dd, pd, preserve_symlinks=1, preserve_mode=0)
                self._rmTree(dd)
                os.symlink(pd, dd)
                self._chmodTree(pd, wdir_wperm, wfile_wperm, False)
            elif ospath.isfile(dd):
                shutil.move(dd, pd)
                os.unlink(dd)
                os.symlink(pd, dd)
                os.chmod(pd, wfile_wperm)
            elif ospath.isdir(pd):
                os.symlink(pd, dd)
                self._chmodTree(pd, wdir_wperm, wfile_wperm, False)
            else:
                os.makedirs(pd, wdir_wperm)
                os.symlink(pd, dd)

        # Build
        if config.get('deployBuild', False):
            self._info('Building project in deployment')
            self.prepare(None)
            self.build()

        # Complete migration
        self.migrate()

        # return back
        self._processDeployDir()
        config = self._config

        # Setup read-only permissions
        self._info('Setting up read-only permissions')

        file_perm = stat.S_IRUSR | stat.S_IRGRP
        dir_perm = file_perm | stat.S_IXUSR | stat.S_IXGRP
        self._chmodTree(tmp, dir_perm, file_perm, True)

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

        if ospath.exists('current'):
            whitelist.append(ospath.basename(os.readlink('current')))

        whitelist += [
            'current',
            'persistent',
            self.DEPLOY_LOCK_FILE,
            self._FUTOIN_JSON,
        ]

        for f in os.listdir('.'):
            (f_noext, f_ext) = ospath.splitext(f)

            if f[0] == '.' or f in whitelist:
                continue

            if ospath.isdir(f):
                self._rmTree(f)
            else:
                os.chmod(f, stat.S_IRWXU)
                os.remove(f)

    def _deployConfig(self):
        self._requireDeployLock()

        self._rebalanceServices()
        self._configServices()

        self._writeDeployConfig()

    def _writeDeployConfig(self):
        self._requireDeployLock()

        config = self._config
        orig_config = self._deploy_config
        new_config = OrderedDict()

        for cv in self.CONFIG_VARS:
            try:
                new_config[cv] = orig_config[cv]
            except KeyError:
                pass

        if config.get('rms', None):
            new_config['rms'] = config['rms']
            new_config['rmsRepo'] = config['rmsRepo']

        new_config['deploy'] = config.get('deploy', {})
        new_config['env'] = orig_config.get('env', {})

        self._info('Writing deployment config in {0}'.format(os.getcwd()))
        self._writeJSONConfig(self._FUTOIN_JSON, new_config)

    def _reloadServices(self):
        self._requireDeployLock()

        # Only service master mode is supported this way
        # Otherwise, deployment invoker is responsible for service reload.
        pid = self._serviceMasterPID()

        if pid:
            os.kill(pid, signal.SIGHUP)

    def _rebalanceServices(self):
        self._info('Re-balancing services')
        from .details.resourcealgo import ResourceAlgo
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

        # DO NOT use realpath as it may point to "old current"
        config['wcDir'] = ospath.join(config['deployDir'], 'current')

        self._mkDir(runtimeDir)
        self._mkDir(tmpDir)

        auto_services = config['deploy']['autoServices']

        for svc in service_list:
            tool = svc['tool']
            t = self._tool_impl[tool]

            if isinstance(t, RuntimeTool):
                cfg_svc = auto_services[svc['name']][svc['instanceId']]
                t.onPreConfigure(config, runtimeDir, svc, cfg_svc)
            else:
                self._errorExit(
                    'Tool "{0}" for "{1}" is not of RuntimeTool type'
                    .format(tool, svc['name']))

    def _processDeployDir(self):
        os.umask(0o027)

        deploy_dir = self._config['deployDir']

        # make sure wcDir is always set to current
        current = self._getDeployCurrent()
        wc_dir = ospath.join(deploy_dir, current)
        self._config['wcDir'] = wc_dir
        self._overrides['wcDir'] = wc_dir

        if not deploy_dir:
            deploy_dir = ospath.realpath('.')
            self._overrides['deployDir'] = deploy_dir

        self._info('Using {0} as deploy directory'.format(deploy_dir))

        placeholder = ospath.join(deploy_dir, self.DEPLOY_LOCK_FILE)

        if not ospath.exists(deploy_dir):
            self._info('Creating deploy directory')
            os.makedirs(deploy_dir)
            open(placeholder, 'w').close()
        elif not ospath.exists(placeholder) and os.listdir(deploy_dir):
            self._errorExit(
                "Deployment dir '{0}' is missing safety placeholder {1}."
                .format(deploy_dir, ospath.basename(placeholder))
            )

        os.chmod(deploy_dir, os.stat(deploy_dir).st_mode | stat.S_IWUSR)

        self._info('Re-initializing config')
        self._initConfig()

        if deploy_dir != os.getcwd():
            print(Coloring.infoLabel('Changing to: ') + Coloring.info(deploy_dir),
                  file=sys.stderr)
            os.chdir(deploy_dir)

        # some tools may benefit of it
        if not self._devserve_mode:
            os.environ['CID_DEPLOY_HOME'] = deploy_dir

        deploy = self._config['deploy']

        if 'user' not in deploy:
            import pwd
            deploy['user'] = pwd.getpwuid(os.geteuid())[0]

        if 'group' not in deploy:
            import grp
            deploy['group'] = grp.getgrgid(os.getegid())[0]


#=============================================================================
class ServiceMixIn(object):
    MASTER_PID_FILE = '.futoin.master.pid'
    RESTART_DELAY = 10
    RESTART_DELAY_THRESHOLD = RESTART_DELAY * 2

    def _serviceAdapt(self):
        if not self._config['adaptDeploy']:
            return

        self._deployLock()
        try:
            self._deploy_setup()
        finally:
            self._deployUnlock()

    def _serviceList(self):
        self._deployLock()
        try:
            self._initConfig()
        finally:
            self._deployUnlock()

        return self._configServiceList(self._config)

    def _configServiceList(self, config):
        entry_points = config.get('entryPoints', {})
        auto_services = config.get('deploy', {}).get('autoServices', {})
        res = []

        for (ep, ei) in entry_points.items():
            if ep not in auto_services:
                self._errorExit(
                    'Unknown service entry point "{0}"'.format(ep))

            i = 0

            for svctune in auto_services[ep]:
                r = copy.deepcopy(ei)
                r['name'] = ep
                r['instanceId'] = i
                r.setdefault('tune', {}).update(svctune)

                if r['tune'].get('socketAddress', None) == '0.0.0.0':
                    r['tune']['socketAddress'] = '127.0.0.1'

                res.append(r)
                i += 1

        return res

    def _serviceListPrint(self):
        for svc in self._serviceList():
            svc_tune = svc['tune']

            #---
            internal = svc_tune.get('internal', False)

            if not internal:
                internal = not bool(svc_tune.get('socketType', False))

            if internal:
                print("{0}\t{1}".format(svc['name'], svc['instanceId']))
                continue

            #---
            socket_type = svc_tune['socketType']

            if socket_type == 'unix':
                socket_addr = svc_tune['socketPath']
            else:
                socket_addr = '{0}:{1}'.format(
                    svc_tune['socketAddress'],
                    svc_tune['socketPort']
                )

            print("\t".join([svc['name'], str(svc['instanceId']),
                             socket_type, socket_addr]))

    def _serviceCommon(self, entry_point, instance_id):
        config = self._config
        entry_points = config.get('entryPoints', {})
        auto_services = config.get('deploy', {}).get('autoServices', {})

        try:
            instance_id = int(instance_id)
        except ValueError:
            self._errorExit('Invalid instance ID "{0}"'.format(instance_id))

        try:
            ep = entry_points[entry_point]
        except KeyError:
            self._errorExit('Unknown entry point "{0}"'.format(entry_point))

        try:
            dep = auto_services[entry_point][instance_id]
        except KeyError:
            self._errorExit(
                'Unknown service entry point "{0}"'.format(entry_point))
        except IndexError:
            self._errorExit('Unknown service entry point "{0}" instance "{1}"'.format(
                entry_point, instance_id))

        res = copy.deepcopy(ep)
        res.setdefault('tune', {}).update(dep)
        return res

    def _serviceStop(self, svc, toolImpl, pid):
        signal.signal(signal.SIGALRM, TimeoutException.alarmHandler)

        tune = svc['tune']
        toolImpl.onStop(self._config, pid, tune)

        try:
            timeout = tune.get(
                'exitTimeoutMS', RuntimeTool.DEFAULT_EXIT_TIMEOUT)
            timeout /= 1000.0
            signal.setitimer(signal.ITIMER_REAL, timeout)

            try:
                os.waitpid(pid, 0)
            except TimeoutException:
                signal.setitimer(signal.ITIMER_REAL, 0)
                os.kill(pid, signal.SIGKILL)
                os.waitpid(pid, 0)
        except OSError:
            pass
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def _serviceMasterPID(self):
        self._requireDeployLock()

        if not ospath.exists(self.MASTER_PID_FILE):
            return None

        try:
            pid = int(self._readTextFile(self.MASTER_PID_FILE))
        except ValueError:
            return None

        try:
            self._masterLock()
            self._masterUnlock()
            return None
        except:
            pass

        return pid

    def _serviceMaster(self):
        svc_list = []
        pid_to_svc = {}

        self._running = True
        self._reload_services = True
        self._interruptable = False

        def serviceExitSignal(*args, **kwargs):
            self._running = False
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            signal.signal(signal.SIGHUP, signal.SIG_IGN)
            signal.signal(signal.SIGUSR1, signal.SIG_IGN)
            signal.signal(signal.SIGUSR2, signal.SIG_IGN)

            if self._interruptable:
                raise KeyboardInterrupt('Exit received')

        def serviceReloadSignal(*args, **kwargs):
            self._reload_services = True

            if self._interruptable:
                raise KeyboardInterrupt('Reload received')

        def childSignal(*args, **kwargs):
            pass

        signal.signal(signal.SIGTERM, serviceExitSignal)
        signal.signal(signal.SIGINT, serviceExitSignal)
        signal.signal(signal.SIGHUP, serviceExitSignal)
        signal.signal(signal.SIGUSR1, serviceReloadSignal)
        signal.signal(signal.SIGUSR2, serviceReloadSignal)

        if self._isMacOS():
            signal.signal(signal.SIGCHLD, signal.SIG_DFL)
        else:
            signal.signal(signal.SIGCHLD, childSignal)

        # Still, it's not safe to assume processes continue
        # to run in set process group.
        # DO NOT use os.killpg()
        #os.setpgid(0, 0)

        # Main loop
        #---
        self._deployLock()
        try:
            current_master = self._serviceMasterPID()

            if current_master:
                self._errorExit(
                    'Master process is already running with PID "{0}"'.format(current_master))

            self._masterLock()
            self._writeTextFile(self.MASTER_PID_FILE,
                                '{0}'.format(os.getpid()))
        finally:
            self._deployUnlock()

        self._info('Starting master process')

        while self._running:
            # Reload services
            #---
            if self._reload_services:
                self._info('Reloading services')

                # Mark shutdown by default
                for svc in svc_list:
                    svc['_remove'] = True

                # Prepare process list
                for newsvc in self._serviceList():
                    for svc in svc_list:
                        for (sk, sv) in newsvc.items():
                            if svc.get(sk, None) != sv:
                                break
                        else:
                            break
                    else:
                        svc = newsvc
                        svc_list.append(newsvc)
                        svc['_pid'] = None
                        svc['_lastExit1'] = self.RESTART_DELAY_THRESHOLD + 1
                        svc['_lastExit2'] = 0

                        tool = svc['tool']
                        t = self._tool_impl[tool]

                        if isinstance(t, RuntimeTool):
                            newsvc['toolImpl'] = t
                        else:
                            self._errorExit(
                                'Tool "{0}" for "{1}" is not of RuntimeTool type'
                                .format(tool, newsvc['name']))

                        self._info('Added "{0}:{1}"'.format(
                            svc['name'], svc['instanceId']))

                    svc['_remove'] = False

                if not len(svc_list):
                    break

                # Kill removed or changed services
                for svc in svc_list:
                    if svc['_remove']:
                        pid = svc['_pid']

                        if pid:
                            self._serviceStop(svc, svc['toolImpl'], pid)
                            pid_to_svc[pid]['_pid'] = None
                            del pid_to_svc[pid]

                        self._info('Removed "{0}:{1}" pid "{2}"'.format(
                            svc['name'], svc['instanceId'], pid))

                svc_list = list(filter(lambda v: not v['_remove'], svc_list))

                # actual reload of services
                for pid in pid_to_svc.keys():
                    svc = pid_to_svc[pid]

                    if svc['tune'].get('reloadable', False):
                        self._info('Reloading "{0}:{1}" pid "{2}"'.format(
                            svc['name'], svc['instanceId'], pid))
                        try:
                            svc['toolImpl'].onReload(
                                self._config, pid, svc['tune'])
                        except OSError:
                            pass
                    else:
                        self._info('Stopping "{0}:{1}" pid "{2}"'.format(
                            svc['name'], svc['instanceId'], pid))
                        self._serviceStop(svc, svc['toolImpl'], pid)

                        del pid_to_svc[pid]
                        svc['_lastExit1'] = self.RESTART_DELAY_THRESHOLD + 1
                        svc['_lastExit2'] = 0
                        svc['_pid'] = None

                self._reload_services = False

            # create children
            for svc in svc_list:
                pid = svc['_pid']
                if pid:
                    continue

                delay = 0

                if (svc['_lastExit1'] - svc['_lastExit2']) < self.RESTART_DELAY_THRESHOLD:
                    delay = self.RESTART_DELAY

                pid = os.fork()

                if pid:
                    svc['_pid'] = pid
                    pid_to_svc[pid] = svc

                    if delay:
                        self._warn('Delaying start "{0}:{1}" pid "{2}"'.format(
                            svc['name'], svc['instanceId'], pid))
                    else:
                        self._info('Started "{0}:{1}" pid "{2}"'.format(
                            svc['name'], svc['instanceId'], pid))
                else:
                    try:
                        signal.signal(signal.SIGTERM, signal.SIG_DFL)
                        signal.signal(signal.SIGINT, signal.SIG_DFL)
                        signal.signal(signal.SIGHUP, signal.SIG_DFL)
                        signal.signal(signal.SIGUSR1, signal.SIG_DFL)
                        signal.signal(signal.SIGUSR2, signal.SIG_DFL)
                        signal.signal(signal.SIGCHLD, signal.SIG_DFL)

                        os.dup2(os.open(os.devnull, os.O_RDONLY), 0)

                        if delay:
                            time.sleep(delay)

                        os.chdir(self._config['wcDir'])

                        svc['toolImpl'].onRun(self._config, svc, [])
                    except Exception as e:
                        self._warn(str(e))
                        import traceback
                        self._warn(str(traceback.format_exc()))
                    finally:
                        sys.stdout.flush()
                        sys.stderr.flush()
                        # Should not be reachable here
                        os._exit(2)

            # Wait for children to exit
            try:
                self._interruptable = True

                if self._reload_services:
                    continue

                if not self._running:
                    break

                (pid, excode) = os.wait()
            except KeyboardInterrupt:
                continue
            except OSError as e:  # macOS
                if e.errno != errno.EINTR:
                    self._warn(str(e))
                continue
            finally:
                self._interruptable = False

            svc = pid_to_svc[pid]
            del pid_to_svc[pid]
            svc['_pid'] = None
            svc['_lastExit2'] = svc['_lastExit1']

            try:
                svc['_lastExit1'] = time.monotonic()
            except:
                times = os.times()
                svc['_lastExit1'] = times[4]

            self._warn('Exited "{0}:{1}" pid "{2}" exit code "{3}"'.format(
                svc['name'], svc['instanceId'], pid, excode))

        # try terminate children
        #---
        self._info('Terminating children')

        for svc in svc_list:
            pid = svc['_pid']

            if pid:
                try:
                    self._info('Terminating "{0}:{1}" pid "{2}"'.format(
                        svc['name'], svc['instanceId'], pid))
                    os.kill(pid, signal.SIGTERM)
                except OSError:
                    del pid_to_svc[pid]
                    self._info('Exited "{0}:{1}" pid "{2}"'.format(
                        svc['name'], svc['instanceId'], pid))

        # try wait children
        #---
        self._info('Waiting for children')
        signal.signal(signal.SIGALRM, TimeoutException.alarmHandler)

        try:
            signal.setitimer(signal.ITIMER_REAL,
                             RuntimeTool.DEFAULT_EXIT_TIMEOUT / 1000.0)

            while len(pid_to_svc) > 0:
                (pid, excode) = os.waitpid(-1, 0)
                svc = pid_to_svc[pid]
                del pid_to_svc[pid]
                self._info('Exited "{0}:{1}" pid "{2}"'.format(
                    svc['name'], svc['instanceId'], pid))
        except TimeoutException:
            self._warn('Timed out waiting for children shutdown')
        except OSError as e:  # macOS
            if e.errno != errno.EINTR:
                self._warn(str(e))
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

        # final kill
        #---
        if pid_to_svc:
            self._info('Killing children')
        for pid in pid_to_svc:
            try:
                svc = pid_to_svc[pid]
                self._info('Killing "{0}:{1}" pid "{2}"'.format(
                    svc['name'], svc['instanceId'], pid))
                os.kill(pid, signal.SIGKILL)
                os.waitpid(pid, 0)
            except OSError as e:
                self._warn(str(e))

        self._info('Master process exit')
        self._masterUnlock()


#=============================================================================
class CIDTool(ServiceMixIn, DeployMixIn, ConfigMixIn, LockMixIn, HelpersMixIn, PathMixIn, UtilMixIn, PackageMixIn):
    TO_GZIP = '\.(js|json|css|svg|txt)$'

    def __init__(self, overrides):
        self._startup_env = dict(os.environ)
        self._tool_impl = None
        self._overrides = overrides
        self._current_dir = None
        self._initLocks()
        self._initConfig()

    @cid_action
    def tag(self, branch, next_version=None):
        mode = 'patch'

        if next_version in ['patch', 'minor', 'major']:
            mode = next_version
            next_version = None

        if next_version and not re.match('^[0-9]+\.[0-9]+\.[0-9]+$', next_version):
            self._errorExit('Valid version format: x.y.z')

        self._processWcDir()

        config = self._config
        vcstool = self._getVcsTool()
        vcsrepo = config['vcsRepo']

        #---
        self._info(
            'Getting source branch {0} from {1}'.format(branch, vcsrepo))
        vcstool.vcsCheckout(config, branch)
        self._initConfig()
        config = self._config

        if 'name' not in config:
            self._errorExit('Failed to detect project "name"')

        # Set new version
        if next_version is None:
            if 'version' in config:
                next_version = config['version']
            else:
                self._errorExit('current project version is unknown')

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

            next_version = '.'.join(next_version)

        config['version'] = next_version

        #---
        self._info('Updating files for release')
        to_commit = []
        self._forEachTool(
            lambda config, t: to_commit.extend(
                t.updateProjectConfig(config, {'version': next_version})
            )
        )

        #---
        if to_commit:
            self._info('Committing updated files')
            message = "Updated for release %s %s" % (
                config['name'], config['version'])
            vcstool.vcsCommit(config, message, to_commit)
        else:
            self._info('Nothing to commit')

        #---
        tag = "v%s" % next_version
        self._info('Creating a tag {0}'.format(tag))
        message = "Release %s %s" % (config['name'], config['version'])
        vcstool.vcsTag(config, tag, message)

        #---
        self._info('Pushing changes to {0}'.format(vcsrepo))
        vcstool.vcsPush(config, [branch, tag])

    @cid_action
    def prepare(self, vcs_ref):
        self._processWcDir()

        config = self._config

        # make a clean checkout
        if vcs_ref:
            vcstool = self._getVcsTool()

            self._info('Getting source ref {0} from {1}'.format(
                vcs_ref, config['vcsRepo']))
            vcstool.vcsCheckout(config, vcs_ref)
            self._initConfig()

        #--
        self._info('Running "prepare" in tools')
        self._forEachTool(
            lambda config, t: t.onPrepare(config),
            base=BuildTool
        )

    @cid_action
    def build(self):
        self._processWcDir()

        self._info('Running "build" in tools')
        self._forEachTool(
            lambda config, t: t.onBuild(config),
            base=BuildTool
        )

    @cid_action
    def package(self):
        self._processWcDir()

        #---
        self._info('Running "package" in tools')
        self._forEachTool(
            lambda config, t: t.onPackage(config),
            base=BuildTool
        )

        #---
        config = self._config
        package_files = config.get('packageFiles', None)

        if package_files is not None:
            self._info(
                'Found binary artifacts from tools: {0}'.format(package_files))
            self._lastPackages = package_files
            return

        # Note: It is assumed that web root is in the package content
        #---
        if config.get('packageGzipStatic', True):
            self._info('Generating GZip files of static content')
            webroot = config.get('webcfg', {}).get('root', '.')
            to_gzip_re = re.compile(self.TO_GZIP, re.I)

            for (path, dirs, files) in os.walk(webroot):
                for f in files:
                    if to_gzip_re.search(f):
                        f = ospath.join(path, f)
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
            package_content = [package_content]

        package_content.sort()
        package_content_cmd = subprocess.list2cmdline(package_content)

        self._info('Generating package from {0}'.format(package_content))

        #---
        if config.get('packageChecksums', True):
            self._info('Generating checksums')
            checksums_file = '.package.checksums'

            checksums = []
            cs_files = []

            for pkg_item in sorted(package_content):
                if ospath.isfile(pkg_item):
                    cs_files.append(pkg_item)

                if ospath.isdir(pkg_item):
                    for (path, dirs, files) in os.walk(pkg_item):
                        for f in sorted(files):
                            f = ospath.join(path, f)
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
                package_content.index('.')
            except ValueError:
                package_content.append(checksums_file)

        #---
        buildTimestamp = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')
        name = config.get('name', 'UNKNOWN').split('/')[-1]
        version = config.get('version', 'UNKNOWN')
        vcs_ref = config.get('vcsRef', None)

        # Note: unless run in clean ci_build process,
        # all builds must be treated as snapshots/CI builds
        if vcs_ref == 'v' + version:
            package_file = '{0}-{1}-{2}'.format(
                name, version, buildTimestamp)
        else:
            vcs_ref = 'UNKNOWN'

            if config.get('vcs', None):
                try:
                    vcstool = self._getVcsTool()
                    vcs_ref = vcstool.vcsGetRevision(config)
                except subprocess.CalledProcessError as e:
                    if config.get('vcsRepo', None):
                        raise e

            package_file = '{0}-CI-{1}-{2}-{3}'.format(
                name, version, buildTimestamp, vcs_ref)

        if 'target' in config:
            package_file += '-{0}'.format(config['target'])

        package_file += '.txz'
        self._info('Creating package {0}'.format(package_file))

        tar_tool = self._getTarTool('xz')
        tar_args = ['cJf', package_file,
                    '--exclude=' + package_file,
                    '--exclude=.git*',
                    '--exclude=.hg*',
                    '--exclude=.svn'] + package_content
        tar_tool.onExec(config['env'], tar_args, False)
        # note, no --exclude-vcs
        self._lastPackages = [package_file]

    @cid_action
    def check(self):
        self._processWcDir()

        self._info('Running "check" in tools')
        self._forEachTool(
            lambda config, t: t.onCheck(config),
            allow_failure=self._config.get('permissiveChecks', False),
            base=TestTool
        )

    @cid_action
    def promote(self, rms_pool, packages):
        self._processWcDir()

        config = self._config
        rmstool = self._getRmsTool()

        pools = rms_pool.split(':', 1)

        if len(pools) == 2:
            self._info('Promoting from {0} to {1} pool: {2}'.format(
                pools[0], pools[1], ', '.join(packages)))
            packages = rmstool.rmsProcessChecksums(config, pools[0], packages)
            rmstool.rmsPromote(config, pools[0], pools[1], packages)
        else:
            self._info('Promoting to {0} pool: {1}'.format(
                rms_pool, ', '.join(packages)))
            rmstool.rmsUpload(config, rms_pool, packages)

    @cid_action
    def migrate(self):
        self._processWcDir()

        self._info('Running "migrate" in tools')
        self._forEachTool(
            lambda config, t: t.onMigrate(config),
            base=MigrationTool
        )

    @cid_action
    def deploy(self, mode, p1=None, p2=None):
        self._processDeployDir()

        self._deployLock()

        try:
            if mode == 'rms':
                self._rms_deploy(p1, p2)
            elif mode == 'vcsref':
                self._vcsref_deploy(p1)
            elif mode == 'vcstag':
                self._vcstag_deploy(p1)
            elif mode == 'setup':
                self._deploy_setup()
            else:
                self._errorExit('Not supported deploy mode: ' + mode)
        finally:
            self._deployUnlock()

    def deploy_set_action(self, name, actions):
        self._processDeployDir()

        dc = self._deploy_config
        dc_actions = dc.setdefault('actions', {})
        dc_actions[name] = actions

        self._deployLock()

        try:
            self._writeDeployConfig()
        finally:
            self._deployUnlock()

    def deploy_set_persistent(self, paths):
        self._processDeployDir()

        dc = self._deploy_config
        persistent = set(dc.get('persistent', []))
        persistent.update(set(paths))
        dc['persistent'] = list(persistent)

        self._deployLock()

        try:
            self._writeDeployConfig()
        finally:
            self._deployUnlock()

    def run(self, command, args):
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
                    svc = copy.deepcopy(ep)
                    svc['name'] = command
                    svc['instanceId'] = 0
                    svc.setdefault('tune', {})

                    import tempfile
                    runtime_dir = tempfile.mkdtemp(prefix='futoin-cid-run')

                    t.onPreConfigure(config, runtime_dir, svc, svc['tune'])
                    t.onRun(config, svc, args)
                else:
                    self._errorExit(
                        'Tool "{0}" for "{1}" does not support "run" command'.format(tool, command))

            elif command in actions:
                _call_actions(command, actions, args)
            else:
                self._errorExit(
                    'Unknown "{0}" action or entry point'.format(command))
        else:
            for cmd in entry_points:
                pid = os.fork()

                if not pid:
                    os.dup2(os.open(os.devnull, os.O_RDONLY), 0)
                    self.run(cmd, None)

            i = len(entry_points)

            while i > 0:
                os.wait()
                i -= 1

    @cid_action
    def ci_build(self, vcs_ref, rms_pool):
        config = self._config
        wcDir = config['wcDir']

        if ospath.exists(wcDir) and wcDir != os.getcwd():
            try:
                dst = '{0}.bak{1}'.format(wcDir, int(time.time()))
                print(Coloring.infoLabel('Renaming: ') +
                      Coloring.info(wcDir + ' to ' + dst),
                      file=sys.stderr)
                os.rename(wcDir, dst)
            except OSError:
                self._rmTree(wcDir)

        self._lastPackages = None
        self.prepare(vcs_ref)
        self.build()
        self.package()
        self.check()

        if rms_pool and self._lastPackages:
            self.promote(rms_pool, self._lastPackages)

    def tool_exec(self, tool, args):
        t = self._tool_impl[tool]
        t.onExec(self._config['env'], args)

    def tool_install(self, tool):
        config = self._config
        env = config['env']

        if self._isExternalToolsSetup(env):
            self._errorExit(
                'environment requires external installation of tools')

        if tool:
            tools = [tool]
        else:
            tools = config['toolOrder']

        self._globalLock()

        for tool in tools:
            t = self._tool_impl[tool]
            t.requireInstalled(env)

        self._globalUnlock()

    def tool_uninstall(self, tool):
        config = self._config
        env = config['env']

        if self._isExternalToolsSetup(env):
            self._errorExit(
                'environment requires external management of tools')

        if tool:
            tools = [tool]
        else:
            tools = reversed(config['toolOrder'])

        self._globalLock()

        for tool in tools:
            t = self._tool_impl[tool]
            if t.isInstalled(env):
                t.uninstallTool(env)

        self._globalUnlock()

    def tool_update(self, tool):
        config = self._config
        env = config['env']

        if self._isExternalToolsSetup(env):
            self._errorExit(
                'environment requires external management of tools')

        if tool:
            tools = [tool]
        else:
            tools = config['toolOrder']

        self._globalLock()

        for tool in tools:
            t = self._tool_impl[tool]
            t.updateTool(env)

        self._globalUnlock()

    def tool_test(self, tool):
        config = self._config
        env = config['env']

        if tool:
            tools = [tool]
        else:
            tools = config['toolOrder']

        for tool in tools:
            t = self._tool_impl[tool]

            if not t.isInstalled(env):
                self._errorExit("Tool '%s' is missing" % tool)

    def tool_env(self, tool):
        config = self._config
        env = config['env']

        if tool:
            tools = [tool]
        else:
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

    def _tool_cmd(self, tool, base, method):
        config = self._config
        t = self._tool_impl[tool]

        if isinstance(t, base):
            t.loadConfig(config)  # see self._initTools()
            getattr(t, method)(config)
        else:
            self._errorExit(
                '{0} tool does not support {1}'.format(tool, method))

    def tool_prepare(self, tool):
        self._tool_cmd(tool, BuildTool, 'onPrepare')

    def tool_build(self, tool):
        self._tool_cmd(tool, BuildTool, 'onBuild')

    def tool_check(self, tool):
        self._tool_cmd(tool, TestTool, 'onCheck')

    def tool_package(self, tool):
        self._tool_cmd(tool, BuildTool, 'onPackage')

        package_files = self._config.get('packageFiles', None)

        if package_files is not None:
            self._info('Package files: {0}'.format(package_files))

    def tool_migrate(self, tool):
        self._tool_cmd(tool, MigrationTool, 'onMigrate')

    def tool_list(self):
        print("List of tools supported by CID:")
        for k in sorted(self._tool_impl.keys()):
            t = self._tool_impl[k]
            doc = t.__doc__.strip() or Coloring.warn('!! Missing documentation.')
            doc = doc.split("\n")[0]
            print(Coloring.infoLabel("  * " + k + ': ') + Coloring.info(doc))
        print('End.')

    def tool_describe(self, tool):
        t = self._tool_impl[tool]

        print(Coloring.infoLabel('* Tool: ') + Coloring.warn(tool))

        auto_detect = t.autoDetectFiles()
        if auto_detect:
            if not isinstance(auto_detect, list):
                auto_detect = [auto_detect]
            print(Coloring.infoLabel('* Auto-detection (files): ') +
                  ', '.join(auto_detect))

        if isinstance(t, VcsTool):
            print(Coloring.infoLabel('* Auto-detected, if set as VCS '))

        if isinstance(t, RmsTool):
            print(Coloring.infoLabel('* Auto-detected, if set as RMS '))

        env_vars = t.envNames()
        if env_vars:
            print(Coloring.infoLabel(
                '* Environment variables: ') + ', '.join(env_vars))

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

    def tool_detect(self):
        config = self._config
        env = config['env']

        for t in config['toolOrder']:
            ver = env.get(t + 'Ver', None)

            if ver:
                print("{0}={1}".format(t, ver))
            else:
                print(t)

    def init_project(self, project_name):
        self._processWcDir()

        if ospath.exists(self._FUTOIN_JSON):
            self._errorExit('futoin.json already exists in project root')

        config = self._config
        new_config = OrderedDict()

        if project_name:
            new_config['name'] = project_name
        elif 'name' not in config:
            new_config['name'] = ospath.basename(config['wcDir'])

        for cv in self.CONFIG_VARS:
            try:
                val = config[cv]

                if val is not None and cv not in new_config:
                    new_config[cv] = val
            except KeyError:
                pass

        self._writeJSONConfig(self._FUTOIN_JSON, new_config)

    def vcs_checkout(self, vcs_ref):
        self._processWcDir()

        config = self._config
        vcstool = self._getVcsTool()

        self._info('Getting source ref {0} from {1}'.format(
            vcs_ref, config['vcsRepo']))
        vcstool.vcsCheckout(config, vcs_ref)

    def vcs_commit(self, msg, files):
        self._processWcDir()

        config = self._config
        vcstool = self._getVcsTool()

        if files:
            self._info('Committing: ' + ', '.join(files))
        else:
            self._info('Committing updated files')
        vcstool.vcsCommit(config, msg, files)

        self._info('Pushing changes to {0}'.format(config['vcsRepo']))
        vcstool.vcsPush(config, None)

    def vcs_branch(self, vcs_ref):
        self._processWcDir()

        config = self._config
        vcstool = self._getVcsTool()

        self._info('Creating new branch {0} in {1}'.format(
            vcs_ref, config['vcsRepo']))
        vcstool.vcsBranch(config, vcs_ref)

    def vcs_merge(self, vcs_ref, cleanup=True):
        self._processWcDir()

        config = self._config
        vcstool = self._getVcsTool()

        self._info('Merging branch {0} from {1}'.format(
            vcs_ref, config['vcsRepo']))
        vcstool.vcsMerge(config, vcs_ref, cleanup)

    def vcs_delete(self, vcs_ref, vcs_cache_dir):
        self._processWcDir()

        config = self._config
        vcstool = self._getVcsTool()

        self._info('Deleting branch {0} from {1}'.format(
            vcs_ref, config['vcsRepo']))
        vcstool.vcsDelete(config, vcs_cache_dir, vcs_ref)

    def vcs_export(self, vcs_ref, dst_path, vcs_cache_dir):
        if ospath.exists(dst_path):
            if os.listdir(dst_path):
                self._errorExit(
                    'Destination directory {0} exists and is not empty'.format(dst_path))
        else:
            os.makedirs(dst_path)

        self._processWcDir()

        config = self._config
        vcstool = self._getVcsTool()

        self._info('Export ref {0} from {1}'.format(
            vcs_ref, config['vcsRepo']))
        vcstool.vcsExport(config, vcs_cache_dir, vcs_ref, dst_path)

    def vcs_tags(self, tag_hint, vcs_cache_dir):
        self._processWcDir()

        config = self._config
        vcstool = self._getVcsTool()

        tag_list = vcstool.vcsListTags(config, vcs_cache_dir, tag_hint)

        if tag_hint:
            tag_list = fnmatch.filter(tag_list, tag_hint)

        self._versionSort(tag_list)

        print("\n".join(tag_list))

    def vcs_branches(self, branch_hint, vcs_cache_dir):
        self._processWcDir()

        config = self._config
        vcstool = self._getVcsTool()

        branch_list = vcstool.vcsListBranches(
            config, vcs_cache_dir, branch_hint)

        if branch_hint:
            branch_list = fnmatch.filter(branch_list, branch_hint)

        self._versionSort(branch_list)

        print("\n".join(branch_list))

    def vcs_reset(self):
        self._processWcDir()

        config = self._config
        vcstool = self._getVcsTool()

        self._info('Reverting all local changes')
        vcstool.vcsRevert(config)

    def vcs_ismerged(self, vcs_ref):
        self._processWcDir()

        config = self._config
        vcstool = self._getVcsTool()

        if vcstool.vcsIsMerged(config, vcs_ref):
            self._info('Branch {0} is merged'.format(vcs_ref))
        else:
            self._info('Branch {0} is NOT merged'.format(vcs_ref))
            sys.exit(1)

    def rms_list(self, rms_pool, package_pattern):
        self._processWcDir()

        config = self._config
        rmstool = self._getRmsTool()

        package_list = rmstool.rmsGetList(config, rms_pool, package_pattern)

        if package_pattern:
            package_list = fnmatch.filter(package_list, package_pattern)

        self._versionSort(package_list)

        print("\n".join(package_list))

    def rms_retrieve(self, rms_pool, package_list):
        self._processWcDir()

        config = self._config
        rmstool = self._getRmsTool()

        self._info('Retrieving packages from RMS...')

        for p in package_list:
            p = ospath.basename(p).split('@', 1)[0]

            if ospath.exists(p):
                self._errorExit('File already exists: {0}'.format(p))

        package_list = rmstool.rmsProcessChecksums(
            config, rms_pool, package_list)
        rmstool.rmsRetrieve(config, rms_pool, package_list)

    def rms_pool_create(self, rms_pool):
        self._processWcDir()

        config = self._config
        rmstool = self._getRmsTool()

        self._info('Creating RMS pool...')

        rmstool.rmsPoolCreate(config, rms_pool)

    def rms_pool_list(self):
        self._processWcDir()

        config = self._config
        rmstool = self._getRmsTool()

        pool_list = rmstool.rmsPoolList(config)

        pool_list = sorted(pool_list)

        print("\n".join(pool_list))

    def service_master(self):
        self._processDeployDir()
        self._serviceAdapt()
        self._serviceMaster()

    def service_list(self):
        self._processDeployDir()
        self._serviceAdapt()
        self._serviceListPrint()

    def service_exec(self, entry_point, instance_id):
        self._processDeployDir()

        config = self._config
        svc = self._serviceCommon(entry_point, instance_id)

        tool = svc['tool']
        t = self._tool_impl[tool]

        if isinstance(t, RuntimeTool):
            os.chdir(config['wcDir'])
            t.onRun(config, svc, [])
        else:
            self._errorExit(
                'Tool "{0}" for "{1}" does not support "service exec" command'.format(tool, entry_point))

    def service_stop(self, entry_point, instance_id, pid):
        self._processDeployDir()

        svc = self._serviceCommon(entry_point, instance_id)

        tool = svc['tool']
        t = self._tool_impl[tool]

        if isinstance(t, RuntimeTool):
            self._serviceStop(svc, t, int(pid))
        else:
            self._errorExit(
                'Tool "{0}" for "{1}" does not support "service stop" command'.format(tool, entry_point))

    def service_reload(self, entry_point, instance_id, pid):
        self._processDeployDir()

        config = self._config
        svc = self._serviceCommon(entry_point, instance_id)

        tool = svc['tool']
        t = self._tool_impl[tool]

        if isinstance(t, RuntimeTool):
            t.onReload(config, int(pid), svc['tune'])
        else:
            self._errorExit(
                'Tool "{0}" for "{1}" does not support "service reload" command'.format(tool, entry_point))

    def devserve(self):
        self._devserve_mode = True

        import tempfile
        deploy_dir = tempfile.mkdtemp(prefix='futoin-cid-devserve')

        try:
            wc_dir = ospath.realpath(self._overrides['wcDir'])
            os.symlink(wc_dir, os.path.join(deploy_dir, 'current'))

            self._overrides['devWcDir'] = wc_dir
            self._config['devWcDir'] = wc_dir

            deploy_dir = os.path.realpath(deploy_dir)
            self._overrides['deployDir'] = deploy_dir
            self._config['deployDir'] = deploy_dir
            self._deployLock()
            self._deployUnlock()

            self._processDeployDir()
            self._config['env']['type'] = 'dev'
            self._serviceAdapt()
            self._serviceListPrint()
            self._serviceMaster()
            self._rmTree(deploy_dir)
            deploy_dir = None
        finally:
            if deploy_dir:
                self._warn(
                    'Left "{0}" for inspection of error'.format(deploy_dir))

    def sudoers(self, entity, skip_key_mgmt):
        if not entity:
            import pwd
            entity = pwd.getpwuid(os.geteuid())[0]

        lines = ['']
        commands = []

        if self._isDebian() or self._isUbuntu():
            lines += [
                '# env whitelist',
                'Defaults  env_keep += "DEBIAN_FRONTEND"',
            ]
            commands += [
                '# package installation only',
                '/usr/bin/apt-get install *',
                '/usr/bin/apt-get update',
                '/usr/bin/apt-add-repository *',
                '/usr/bin/dpkg -i *',
            ]

            if not skip_key_mgmt:
                commands += [
                    '',
                    '# signing key setup',
                    '/usr/bin/apt-key add *',
                ]

        elif self._isFedora():
            commands += [
                '# package installation only',
                '/usr/bin/dnf install *',
                '/usr/bin/dnf config-manager --add-repo *',
            ]

            if not skip_key_mgmt:
                commands += [
                    '',
                    '# signing key setup',
                    '/usr/bin/rpm --import *',
                ]

        elif self._isCentOS() or self._isOracleLinux() or self._isRHEL():
            commands += [
                '# package installation only',
                '/usr/bin/yum install *',
                '/usr/bin/yum-config-manager --add-repo *',
            ]

            if not skip_key_mgmt:
                commands += [
                    '',
                    '# signing key setup',
                    '/usr/bin/rpm --import *',
                ]

        elif self._isOpenSUSE() or self._isSLES():
            commands += [
                '# package installation only',
                '/usr/bin/zypper install *',
                '/usr/bin/zypper addrepo *',
            ]

            if not skip_key_mgmt:
                commands += [
                    '',
                    '# signing key setup',
                    '/bin/rpm --import *',
                ]

        elif self._isArchLinux():
            commands += [
                '# package installation only',
                '/usr/bin/pacman *',
            ]

        elif self._isGentoo():
            commands += [
                '# package installation only',
                '/usr/bin/emerge *',
            ]

        elif self._isAlpineLinux():
            commands += [
                '# package installation only',
                '/sbin/apk add *',
                '/sbin/apk update',
                '/usr/bin/npm *',
                '/usr/bin/tee -a /etc/apk/repositories',
            ]

        elif self._isMacOS():
            commands += [
                '# case for global brew install',
                '/usr/local/bin/brew install *',
                '/usr/local/bin/brew cask install *',
                '# note: security problem, if optional URL paremeter is used',
                '/usr/local/bin/brew tap homebrew/*',
                '/usr/local/bin/brew tap caskroom/*',
                '# lesser problem',
                '/usr/local/bin/brew unlink *',
            ]

            if not skip_key_mgmt:
                commands += [
                    '',
                    '# insecure, but required for local brew cask',
                    'SETENV: /usr/sbin/installer *',
                    'SETENV: /usr/sbin/pkgutil *',
                    'SETENV: /usr/libexec/PlistBuddy *',
                    'SETENV: /usr/bin/xargs -0 -- /bin/rm *',
                    'SETENV: /bin/mv *',
                    'SETENV: /bin/ln *',
                    'SETENV: /bin/chmod *',
                    'SETENV: /bin/chown *',
                    'SETENV: /bin/rm *',
                    'SETENV: /bin/rmdir *',
                ]

        else:
            self._errorExit('Unfortunately this OS is not fully supported yet')

        if ospath.exists('/bin/systemctl'):
            commands += [
                '',
                '# start of services',
                '/bin/systemctl start *',
            ]

        if ospath.exists('/sbin/rc-service'):
            commands += [
                '',
                '# start of services',
                '/sbin/rc-service * start',
            ]

        if self._isLinux():
            commands += [
                '',
                '# allow access to Docker (may have no sense)',
                '/usr/bin/docker *',
            ]

        commands += [
            '',
            '# virtual env bootstrap',
            '/usr/bin/pip install *',
        ]

        lines.append('')

        for c in commands:

            if c and c[0] != '#':
                lines.append('{0} ALL=(ALL) NOPASSWD: {1}'.format(entity, c))
            else:
                lines.append(c)

        lines.append('')
        lines = "\n".join(lines)
        print(lines)

    def builddep(self, deps):
        tools = set(self._tool_impl.keys()) & set(deps)
        self._config['tools'] = dict([(t, True) for t in tools])
        self._initTools()

        env = self._config['env']
        self._requireBuildDep(env, deps)
