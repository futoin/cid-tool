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

from collections import OrderedDict


class ConfigMixIn(DataSlots):
    try:
        __str_type = (str, unicode)
    except NameError:
        __str_type = (str, )

    CONFIG_VARS = OrderedDict([
        ('name', __str_type),
        ('version', __str_type),
        ('vcs', __str_type),
        ('vcsRepo', __str_type),
        ('deployBuild', bool),
        ('permissiveChecks', bool),
        ('rms', __str_type),
        ('rmsRepo', __str_type),
        ('rmsPool', __str_type),
        ('tools', dict),
        ('toolTune', dict),
        ('package', list),
        ('packageGzipStatic', bool),
        ('packageChecksums', bool),
        ('persistent', list),
        ('writable', list),
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
        ('type', __str_type),
        ('persistentDir', __str_type),
        ('vars', dict),
        ('plugins', dict),
        ('pluginPacks', list),
        ('externalSetup', (bool,) + __str_type),
        ('externalServices', list),
        ('timeouts', dict),
    ])

    __slots__ = ()

    def __init__(self):
        super(ConfigMixIn, self).__init__()
        self._startup_env = dict(self._environ)
        self._overrides = None

    def _origEnv(self):
        return self._startup_env

    def __resetProcessEnv(self):
        os = self._os
        orig_env = self._startup_env
        environ = self._environ

        for (k, v) in orig_env.items():
            environ[k] = v

        to_del = set(environ.keys()) - set(orig_env.keys())

        for k in to_del:
            del environ[k]

    def __initUserHome(self):
        if 'HOME' not in self._environ:
            self._environ['HOME'] = self._ext.pwd.getpwuid(self._os.geteuid())[
                5]

    def __exportVar(self, environ, key, value):
        if isinstance(value, bool):
            value = value and '1' or ''
        elif isinstance(value, int):
            value = str(value)

        try:
            self._environ[key] = value
        except:
            self._warn('Export failed: {0}'.format(key))
            raise

    def _initConfig(self, startup=False):
        ospath = self._ospath
        os = self._os

        if not startup:
            self.__resetProcessEnv()

        errors = []

        # --
        environ = self._environ
        self.__initUserHome()
        user_home = environ['HOME']
        user_home = ospath.realpath(user_home)
        user_config_path = ospath.join(user_home, self._FUTOIN_USER_JSON)

        if not ospath.exists(user_config_path) and user_home != os.getcwd():
            user_config_path = ospath.join(user_home, self._FUTOIN_JSON)

        user_config_path = ospath.realpath(user_config_path)

        global_config_file = ospath.join(
            '/', 'etc', 'futoin', self._FUTOIN_JSON)
        global_config_file = ospath.realpath(global_config_file)

        deploy_config_file = None
        project_config_file = None
        deploy_dir = self._overrides.get('deployDir', None)

        if startup:
            pass
        elif deploy_dir:
            current = self._getDeployCurrent()
            deploy_config_file = ospath.join(deploy_dir, self._FUTOIN_JSON)
            deploy_config_file = ospath.realpath(deploy_config_file)
            project_config_file = ospath.join(
                deploy_dir, current, self._FUTOIN_JSON)
            project_config_file = ospath.realpath(project_config_file)
        else:
            project_config_file = ospath.realpath(self._FUTOIN_JSON)

            if not ospath.exists(project_config_file):
                (cwd, _) = ospath.split(os.getcwd())

                while cwd != '/' and cwd != user_home:
                    project_config_file = ospath.join(
                        cwd, self._FUTOIN_JSON)
                    if ospath.exists(project_config_file):
                        break
                    (cwd, _) = ospath.split(cwd)

            cwd = ospath.dirname(project_config_file)
            (parent_dir, _) = ospath.split(cwd)
            curr_lock_file = ospath.join(cwd, self._DEPLOY_LOCK_FILE)
            parent_lock_file = ospath.join(parent_dir, self._DEPLOY_LOCK_FILE)
            override_project_config = False

            if ospath.exists(curr_lock_file):
                deploy_dir = ospath.realpath(cwd)
                override_project_config = True
            elif ospath.exists(parent_lock_file):
                deploy_dir = ospath.realpath(parent_dir)

            if deploy_dir:
                self._overrides['deployDir'] = deploy_dir
                deploy_config_file = ospath.join(
                    deploy_dir, self._FUTOIN_JSON)

                if override_project_config:
                    current = self._getDeployCurrent()
                    current_dir = ospath.join(deploy_dir, current)
                    project_config_file = ospath.join(
                        current_dir, self._FUTOIN_JSON)

        # --
        gc = {'env': {}}
        uc = {'env': {}}
        dc = {}
        pc = {}

        gc = self._pathutil.loadJSONConfig(global_config_file, gc)

        if user_config_path not in (deploy_config_file, project_config_file):
            uc = self._pathutil.loadJSONConfig(user_config_path, uc)

        if not startup:
            if project_config_file != deploy_config_file:
                pc = self._pathutil.loadJSONConfig(project_config_file, pc)

            if deploy_config_file:
                dc = self._pathutil.loadJSONConfig(deploy_config_file, dc)

        # ---
        self._global_config = gc
        self._user_config = uc

        if startup:
            self._deploy_config = None
            self._project_config = None
        else:
            self._deploy_config = dc
            self._project_config = pc

        # --

        config = dict(pc)

        # Deployment config can override project config
        for (k, v) in dc.items():
            if k in ('deploy', 'env'):
                continue
            elif k == 'entryPoints':
                config_epoints = config.setdefault('entryPoints', {})

                for (ename, edef) in v.items():
                    cep = config_epoints.setdefault(ename, {})

                    for (epk, epv) in edef.items():
                        if epk == 'tune':
                            cep_tune = cep.setdefault('tune', {})
                            cep_tune.update(epv)
                        else:
                            cep[epk] = epv
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
            elif k == 'tools':
                config_tools = config.setdefault('tools', {})
                config_tools.update(v)
            elif k == 'toolTune':
                config_tooltune = config.setdefault('toolTune', {})

                for (tname, ttune) in v.items():
                    ctt = config_tooltune.setdefault(tname, {})
                    ctt.update(ttune)
            else:
                config[k] = v

        self.__sanitizeConfig(config, errors)

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

        self.__initEnv(env)

        config['env'] = env
        self._env = env
        config.update(self._overrides)

        if startup:
            self._config = None
        else:
            self._config = config

        self._initTools()

        #
        if not startup:
            entry_points = config.get('entryPoints', {})

            for (en, ep) in entry_points.items():
                t = self._getTool(ep['tool'])
                ep_tune = ep.setdefault('tune', {})

                for (tk, tv) in t.tuneDefaults(env).items():
                    ep_tune.setdefault(tk, tv)

            # run again to check tuneDefaults() from plugins
            self.__sanitizeEntryPoints(entry_points, errors)

        # ---
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

        self.__sanitizeDeployConfig(config, errors)

        # ---
        if not startup:
            # there is no point to export variables provided in env
            # or global configs.
            export_env = {}

            for tool in config.get('toolOrder', []):
                self._getTool(tool).exportEnv(env, export_env)

            environ = self._environ

            for (k, v) in export_env.items():
                self.__exportVar(environ, k, v)

        # ---
        if errors:
            self._errorExit(
                "Configuration issues are found:\n\n* " +
                "\n* ".join(set(errors)))

    def __sanitizeConfig(self, config, errors):
        conf_vars = self.CONFIG_VARS
        to_del = []

        for (k, v) in config.items():
            if k not in conf_vars:
                self._warn('Removing unknown config variable "{0}"'.format(k))
                to_del.append(k)
            elif not isinstance(v, conf_vars[k]):
                req_t = conf_vars[k]
                if isinstance(req_t, tuple):
                    req_t = req_t[0]

                errors.append(
                    'Config variable "{0}" type "{1}" is not instance of "{2}"'
                    .format(k, v.__class__.__name__, req_t.__name__)
                )
        for k in to_del:
            del config[k]

        # ---
        # Make sure futoinTool is enabled, if futoin.json is present.
        # Otherwise, auto-detection gets disabled and futoin.json is not
        # updated
        tools = config.get('tools', None)

        if tools and 'futoin' not in tools:
            tools['futoin'] = True

        # ---
        entry_points = config.get('entryPoints', None)

        if entry_points:
            self.__sanitizeEntryPoints(entry_points, errors)

        # ---
        toolTune = config.get('toolTune', None)

        if toolTune:
            for (tn, tune) in toolTune.items():
                if not isinstance(tune, dict):
                    errors.append(
                        'Tool tune "{0}" is not of map type'.format(tn))

    def __sanitizeEntryPoints(self, entry_points, errors):
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
                        self.__sanitizeMemory(
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

    def __sanitizeDeployConfig(self, dc, errors):
        deploy = dc.get('deploy', {})

        if 'maxTotalMemory' in deploy:
            maxTotalMemory = deploy['maxTotalMemory']

            self.__sanitizeMemory('deploy/maxTotalMemory',
                                  maxTotalMemory, errors)

        if 'maxCpuCount' in deploy:
            val = deploy['maxCpuCount']

            if not isinstance(val, int) or val <= 0:
                errors.append(
                    '"deploy/maxCpuCount" must be a positive integer')

    def __sanitizeMemory(self, key, val, errors):
        try:
            self._configutil.parseMemory(val)
        except:
            errors.append(
                'Memory value "{0}" must be positive '
                'integer with B, K, M or G postfix (e.g. "16M")'
                .format(key))

    def __initEnv(self, env):
        env.setdefault('type', 'prod')
        env.setdefault('vars', {})
        env.setdefault('plugins', {})
        env.setdefault('pluginPacks', [])
        env.setdefault('externalSetup', False)
        env.setdefault('externalServices', [])

        timeouts = env.setdefault('timeouts', {})
        timeouts.setdefault('connect', 10)
        read_to = timeouts.setdefault('read', 60)
        timeouts.setdefault('total', read_to * 60)

        pathutil = self._pathutil
        env.setdefault('binDir', pathutil.safeJoin(
            self._environ['HOME'], 'bin'))
        pathutil.addBinPath(env['binDir'])

        # ---
        env_vars = self.FUTOIN_ENV_VARS

        for (k, v) in env.items():
            if k not in env_vars:
                try:
                    self.__exportVar(self._environ, k, v)
                except:
                    pass
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

    def _processWcDir(self):
        ospath = self._ospath
        os = self._os

        wcDir = self._overrides['wcDir']

        try:
            os.makedirs(wcDir)
        except OSError:
            if not ospath.exists(wcDir):
                raise

        if wcDir != os.getcwd():
            self._infoLabel('Changing to: ', wcDir)
            os.chdir(wcDir)
            self._overrides['wcDir'] = os.getcwd()
            self._initConfig()
        elif self._config is None:
            self._initConfig()

    def _exportConfig(self, orig_config):
        new_config = OrderedDict()

        for cv in self.CONFIG_VARS:
            try:
                val = orig_config[cv]

                if val is not None:
                    new_config[cv] = val
            except KeyError:
                pass

        return new_config
