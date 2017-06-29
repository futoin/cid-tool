
import os
import glob
import copy

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

    def getDeps(self):
        return ['php']

    def tuneDefaults(self):
        return {
            'minMemory': '1M',
            'connMemory': '8M',
            'debugConnOverhead': '24M',
            'socketTypes': ['unix', 'tcp'],
            'socketType': 'unix',
            'socketProtocol': 'fcgi',
            'scalable': True,
            'multiCore': True,
            'maxInstances': 2,
            'maxRequestSize': '1M',
        }

    def _installTool(self, env):
        php_ver = env['phpVer']

        if php_ver == self.SYSTEM_VER:
            self._systemDeps()
            return

        if env['phpBinOnly']:
            self._installBinaries(env)
            return

    def _installBinaries(self, env):
        ver = env['phpVer']

        if self._isDebian() or self._isUbuntu():
            self._requireDeb('php{0}-fpm'.format(ver))

        elif self._isSCLSupported():
            if self._isPHPSCL(env):
                ver = ver.replace('.', '')

                self._requireSCL()

                self._requireYum([
                    'rh-php{0}-php-fpm'.format(ver),
                ])
            else:
                self._errorExit('Only SCL packages are supported so far')
        else:
            self._systemDeps()

    def _isPHPSCL(self, env):
        return env['phpfpmVer'] in ('5.6', '7.0')

    def _systemDeps(self):
        self._requireDeb(['php.*-fpm'])
        self._requireZypper(['php*-fpm'])
        self._requireYum(['php-fpm'])
        self._requirePacman(['php-fpm'])
        self._requireApkCommunity()
        self._requireApk(['php7-fpm'])

    def envNames(self):
        return ['phpfpmBin', 'phpfpmVer']

    def initEnv(self, env):
        php_ver = env['phpVer']
        phpfpm_ver = env.setdefault('phpfpmVer', php_ver)

        if php_ver != phpfpm_ver:
            self._errorExit(
                'PHP mismatch FPM version {0} != {1}'.format(php_ver, phpfpm_ver))

        if 'phpBin' not in env:
            return

        php_bin = env['phpBin']

        if env['phpBinOnly']:
            bin_name = 'php-fpm'

            if self._isDebian() or self._isUbuntu():
                bin_name = 'php-fpm' + php_ver

        else:
            bin_name = '{0}-fpm'.format(os.path.basename(php_bin))

        #--
        phpfpm_bin = os.path.realpath(
            os.path.join(php_bin, '..', '..', 'sbin',
                         '{0}*'.format(bin_name))
        )
        phpfpm_bin = glob.glob(phpfpm_bin)

        if phpfpm_bin:
            env['phpfpmBin'] = phpfpm_bin[0]
            self._have_tool = True
            return

        # fallback, find any
        #---
        phpfpm_bin = self._which(bin_name)

        if phpfpm_bin:
            env['phpfpmBin'] = phpfpm_bin
            self._have_tool = True
            return

    def onPreConfigure(self, config, runtime_dir, svc, cfg_svc_tune):
        env = config['env']
        deploy = config['deploy']
        name_id = '{0}-{1}'.format(svc['name'], svc['instanceId'])

        svc_tune = svc['tune']
        max_clients = svc_tune['maxConnections']

        # conf location
        fpm_conf = "phpfpm-{0}.conf".format(name_id)
        fpm_conf = os.path.join(runtime_dir, fpm_conf)

        php_conf = "php-{0}.ini".format(name_id)
        php_conf = os.path.join(runtime_dir, php_conf)

        # Save location to deployment config
        cfg_svc_tune.update({
            'fpmConf': fpm_conf,
            'phpConf': php_conf,
        })

        #
        log_level = 'error'
        if self._isMacOS():
            # TODO: find solution
            error_log = '/dev/null'
        else:
            error_log = '/proc/self/fd/2'
        display_errors = 'Off'
        error_reporting = 'E_ALL & ~E_NOTICE & ~E_STRICT & ~E_DEPRECATED'

        if config['env']['type'] != 'prod':
            log_level = 'notice'
            display_errors = 'On'
            error_reporting = 'E_ALL | E_STRICT'

        #
        fpm_ini = svc_tune.get('config', {})
        fpm_ini = copy.deepcopy(fpm_ini)

        #
        cid_tune = svc_tune.get('cid', {})

        #
        global_ini = fpm_ini.setdefault('global', {})
        global_ini.setdefault('error_log', error_log)
        global_ini.setdefault('log_level', log_level)
        global_ini.setdefault('syslog.ident', name_id)
        global_ini['daemonize'] = 'no'
        global_ini['rlimit_files'] = svc_tune['maxFD']

        if os.path.exists('/bin/systemctl'):
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

        self._writeIni(fpm_conf, fpm_ini)

        #
        tmp_dir = os.path.join(deploy['tmpDir'], 'php')
        self._mkDir(tmp_dir)

        upload_dir = os.path.join(deploy['tmpDir'], 'phpupload')
        self._mkDir(upload_dir)

        #
        php_ini = svc_tune.get('phpini', {})
        php_ini = php_ini.copy()

        php_ini.setdefault('sys_temp_dir', tmp_dir)
        php_ini.setdefault(
            'memory_limit', self._parseMemory(svc_tune['connMemory']))
        php_ini.setdefault('expose_php', 'Off')
        php_ini.setdefault('zend.multibyte', 'On')
        php_ini.setdefault('zend.script_encoding', 'UTF-8')
        php_ini.setdefault('default_charset', 'UTF-8')
        php_ini.setdefault('register_globals', 'Off')
        php_ini.setdefault('include_path', '.')
        php_ini.setdefault('error_log', error_log)
        php_ini.setdefault('catch_workers_output', 'on')
        php_ini.setdefault('display_errors', display_errors)
        php_ini.setdefault('display_startup_errors', display_errors)
        php_ini.setdefault('error_reporting', error_reporting)
        php_ini.setdefault('file_uploads', 'On')
        php_ini.setdefault('upload_tmp_dir', upload_dir)
        request_size_limit = self._parseMemory(svc_tune['maxRequestSize'])
        php_ini['upload_max_filesize'] = request_size_limit
        php_ini['post_max_size'] = request_size_limit

        if config['env']['type'] != 'dev':
            php_ini.setdefault('open_basedir', config['deployDir'])

        # note: basic extensions are loaded from system (PHP_INI_SCAN_DIR)
        for k in ('extension', 'zend_extension'):
            if k in cid_tune:
                php_ini[k] = cid_tune

        self._writeIni(php_conf, {'php': php_ini})

        # Validate
        self._callExternal([
            env['phpfpmBin'],
            '-c', php_conf,
            '--fpm-config', fpm_conf,
            '--test',
        ])

    def onRun(self, config, svc, args):
        env = config['env']
        svc_tune = svc['tune']
        self._callInteractive([
            env['phpfpmBin'],
            '-c', svc_tune['phpConf'],
            '--fpm-config', svc_tune['fpmConf'],
            '--nodaemonize',
        ] + args)
