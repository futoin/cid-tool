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

from ..runtimetool import RuntimeTool


class phpfpmTool(RuntimeTool):
    """PHP is a popular general-purpose scripting language that is especially suited to web development.

Home: http://php.net/

This tool provides PHP-FPM based website entry point support.
It means any PHP file in project can be executed with all consequences.

Use .tune.config for php-fpm.conf tuning - dicts of dicts representing ini file.
* 'global' -> FPM config
* 'pool' -> pool config

Use .tune.cid for default algorithm tuning
* 'extension' = [] - list of additional extensions to load
* 'zend_extension' - [] - list of additional zend extensions to load

Use .tune.phpini for php.ini tuning - dict representing ini file options.

Note: system php.ini is ignored, but all extensions are automatically loaded from system scan dir.
Note: file upload is OFF by default.
"""
    __slots__ = ()

    def getDeps(self):
        return ['php']

    def tuneDefaults(self, env):
        return {
            'internal': True,
            'minMemory': '1M',
            'connMemory': '16M',
            'debugConnOverhead': '16M',
            'socketTypes': ['unix', 'tcp'],
            'socketType': 'unix',
            'socketProtocol': 'fcgi',
            'scalable': True,
            'reloadable': False,
            'multiCore': True,
            'maxInstances': 2,
            'maxRequestSize': '1M',
        }

    def _installTool(self, env):
        self._phputil.installExtensions(env, 'opcache', True)

        php_ver = env['phpVer']

        if not env['phpSourceBuild']:
            self._installBinaries(env)
            return

    def _installBinaries(self, env):
        ver = env['phpVer']
        base_pkg = self._phputil.basePackage(ver)

        detect = self._detect

        if detect.isDebian() or detect.isUbuntu():
            self._install.deb('{0}-fpm'.format(base_pkg))

        elif detect.isSCLSupported():
            if self._phputil.isIUSVer(ver):
                self._install.yum('{0}-fpm'.format(base_pkg))
            else:
                self._install.yum('{0}-php-fpm'.format(base_pkg))

        else:
            fpm_pkg = '{0}-fpm'.format(base_pkg)
            # self._install.brew(nothing)
            self._install.zypper(fpm_pkg)
            self._install.yum(fpm_pkg)
            self._install.pacman(fpm_pkg)
            self._install.apk(fpm_pkg)

    def envNames(self):
        return ['phpfpmBin', 'phpfpmVer', 'phpfpmErrorLog']

    def _setFPMBin(self, env, phpfpm_bin):
        os = self._os
        ospath = self._ospath
        pathutil = self._pathutil

        if 'phpFakeBinDir' in env:
            php_bin_dir = env['phpFakeBinDir']
            orig_bin = phpfpm_bin
            phpfpm_bin = ospath.join(php_bin_dir, 'php-fpm')

            if ospath.exists(php_bin_dir) and ospath.islink(phpfpm_bin) and os.readlink(phpfpm_bin) == orig_bin:
                pass
            else:
                pathutil.rmTree(phpfpm_bin)
                os.symlink(orig_bin, phpfpm_bin)
        else:
            pathutil.addBinPath(ospath.dirname(phpfpm_bin), True)

        env['phpfpmBin'] = phpfpm_bin
        self._have_tool = True

    def initEnv(self, env):
        ospath = self._ospath
        detect = self._detect
        phputil = self._phputil

        php_ver = env['phpVer']
        phpfpm_ver = env.setdefault('phpfpmVer', php_ver)

        if php_ver != phpfpm_ver:
            self._errorExit(
                'PHP mismatch FPM version {0} != {1}'.format(php_ver, phpfpm_ver))
        # ---
        if self._detect.isMacOS():
            # TODO: find solution
            error_log = '/dev/null'
        else:
            error_log = '/proc/self/fd/2'

        env.setdefault('phpfpmErrorLog', error_log)

        # ---
        if 'phpBin' not in env:
            return

        php_bin = env['phpBin']

        if env['phpSourceBuild'] or detect.isSCLSupported():
            phpfpm_bin = ospath.join(php_bin, '..', '..', 'sbin', 'php-fpm')
            phpfpm_bin = ospath.realpath(phpfpm_bin)

            if ospath.exists(phpfpm_bin):
                self._setFPMBin(env, phpfpm_bin)
                return
        else:
            bin_name = 'php-fpm'

            if detect.isDebian() or detect.isUbuntu():
                bin_name = 'php-fpm' + php_ver

            elif detect.isArchLinux():
                if phputil.isArchLatest(php_ver):
                    bin_name = 'php-fpm'
                else:
                    bin_name = 'php{0}-fpm'.format(php_ver.replace('.', ''))

            elif detect.isAlpineLinux():
                if phputil.isAlpineSplit():
                    bin_name = 'php-fpm' + php_ver[0]
                else:
                    bin_name = 'php-fpm'

            # --
            phpfpm_bin = ospath.realpath(
                ospath.join(php_bin, '..', '..', 'sbin',
                            '{0}*'.format(bin_name))
            )
            phpfpm_bin = self._ext.glob.glob(phpfpm_bin)

            if phpfpm_bin:
                self._setFPMBin(env, phpfpm_bin[0])
                return

            # fallback, find any
            # ---
            self._pathutil.addBinPath('/usr/sbin')
            phpfpm_bin = self._pathutil.which(bin_name)

            if phpfpm_bin:
                self._setFPMBin(env, phpfpm_bin)
                return

    def onPreConfigure(self, config, runtime_dir, svc, cfg_svc_tune):
        ospath = self._ospath
        configutil = self._configutil
        env = config['env']
        deploy = config['deploy']
        name_id = '{0}-{1}'.format(svc['name'], svc['instanceId'])

        svc_tune = svc['tune']
        max_clients = svc_tune['maxConnections']

        # conf location
        fpm_conf = "phpfpm-{0}.conf".format(name_id)
        fpm_conf = ospath.join(runtime_dir, fpm_conf)

        php_conf = "php-{0}.ini".format(name_id)
        php_conf = ospath.join(runtime_dir, php_conf)

        # Save location to deployment config
        cfg_svc_tune.update({
            'fpmConf': fpm_conf,
            'phpConf': php_conf,
        })

        #
        log_level = 'error'
        error_log = env['phpfpmErrorLog']
        display_errors = 'Off'
        error_reporting = 'E_ALL & ~E_NOTICE & ~E_STRICT & ~E_DEPRECATED'

        if config['env']['type'] != 'prod':
            log_level = 'notice'
            display_errors = 'On'
            error_reporting = 'E_ALL | E_STRICT'

        #
        fpm_ini = svc_tune.get('config', {})
        fpm_ini = self._ext.copy.deepcopy(fpm_ini)

        #
        cid_tune = svc_tune.get('cid', {})

        #
        global_ini = fpm_ini.setdefault('global', {})
        global_ini.setdefault('error_log', error_log)
        global_ini.setdefault('log_level', log_level)
        global_ini.setdefault(
            'syslog.ident', configutil.syslogTag(env, name_id))
        global_ini['daemonize'] = 'no'
        global_ini['rlimit_files'] = svc_tune['maxFD']

        if ospath.exists('/bin/systemctl'):
            global_ini['systemd_interval'] = '0'

        #
        pool_ini = fpm_ini.setdefault('pool', {})

        socket_type = svc_tune['socketType']

        if socket_type == 'unix':
            pool_ini['listen'] = svc_tune['socketPath']
        elif socket_type == 'tcp':
            pool_ini['listen'] = '{0}:{1}'.format(
                svc_tune['socketAddress'], svc_tune['socketPort'])
        else:
            self._errorExit(
                'Unsupported socket type "{0}" for "{1}"'.format(socket_type, name_id))

        pool_ini.setdefault('listen.backlog', -1)
        pool_ini['user'] = deploy['user']
        pool_ini['group'] = deploy['group']
        pool_ini.setdefault('pm', 'static')
        pool_ini['pm.max_children'] = max_clients
        pool_ini['chdir'] = config['wcDir']
        pool_ini.setdefault('clear_env', 'yes')
        pool_ini.setdefault('catch_workers_output', 'on')

        self._pathutil.writeIni(fpm_conf, fpm_ini)

        #
        tmp_dir = ospath.join(deploy['tmpDir'], 'php')
        self._pathutil.mkDir(tmp_dir)

        upload_dir = ospath.join(deploy['tmpDir'], 'phpupload')
        self._pathutil.mkDir(upload_dir)

        #
        php_ini = svc_tune.get('phpini', {})
        php_ini = php_ini.copy()

        php_ini.setdefault('sys_temp_dir', tmp_dir)
        php_ini.setdefault(
            'memory_limit', configutil.parseMemory(svc_tune['connMemory']))
        php_ini.setdefault('expose_php', 'Off')
        php_ini.setdefault('zend.multibyte', 'On')
        php_ini.setdefault('zend.script_encoding', 'UTF-8')
        php_ini.setdefault('default_charset', 'UTF-8')
        php_ini.setdefault('register_globals', 'Off')
        php_ini.setdefault('include_path', '.')
        php_ini.setdefault('error_log', error_log)
        php_ini.setdefault('display_errors', display_errors)
        php_ini.setdefault('display_startup_errors', display_errors)
        php_ini.setdefault('error_reporting', error_reporting)
        php_ini.setdefault('file_uploads', 'On')
        php_ini.setdefault('upload_tmp_dir', upload_dir)
        request_size_limit = configutil.parseMemory(
            svc_tune['maxRequestSize'])
        php_ini['upload_max_filesize'] = request_size_limit
        php_ini['post_max_size'] = request_size_limit

        if config['env']['type'] != 'dev':
            php_ini.setdefault('open_basedir', config['deployDir'])

        # note: basic extensions are loaded from system (PHP_INI_SCAN_DIR)
        for k in ('extension', 'zend_extension'):
            if k in cid_tune:
                php_ini[k] = cid_tune

        self._pathutil.writeIni(php_conf, {'php': php_ini})

        # Validate
        self._executil.callExternal([
            env['phpfpmBin'],
            '-c', php_conf,
            '--fpm-config', fpm_conf,
            '--test',
        ])

    def onRun(self, config, svc, args):
        env = config['env']
        svc_tune = svc['tune']
        self._executil.callInteractive([
            env['phpfpmBin'],
            '-c', svc_tune['phpConf'],
            '--fpm-config', svc_tune['fpmConf'],
            '--nodaemonize',
        ] + args)
