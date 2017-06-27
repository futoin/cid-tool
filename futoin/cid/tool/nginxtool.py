
import os

from ..runtimetool import RuntimeTool
from ..details.nginx import *

__all__ = 'nginxTool'


class nginxTool(RuntimeTool):
    """nginx [engine x], originally written by Igor Sysoev.
Home: http://nginx.org

nginx support is targeted only cases when server is run behind
reverse proxy or level 7 load balancer. It's NOT configured
for frontend cases !!!

Note: nginxVer supports only "stable" or "mainline" trying to setup from nginx.org
repos as far as possible. Please remove OS-supplied nginx, if installed.

Tune possibilities through .tune.config - representing dict-based tree structure:
* global directives
* .events
    * events directives
* .http
    * http-level directives
    * .server - the only vhost
        * server-level directives

It's possible to override automatic variables in some cases.

Additional logic tuning is available through .tune.cid:
* .listenOptions = 'default_server deferred'
* .serveStatic = true
* .upstreamZoneSize = 64k - shared memory for upstream zones
* .upstreamFailTimeout = 10 - upstream failure timeout
* .upstreamQueue = None - paramaters to "queue", if set (commercial)
* .upstreamKAPercent = 25 - Keep-Alive percent
* .proxyProtocol = False - enable binary proxy-protocol



Additional notes:
* proxy buffering is disabled and assumed to be part of front- or middle- balancers

"""
    _GPG_KEY = GPG_KEY

    def envNames(self):
        return ['nginxBin', 'nginxVer', 'nginxBaseUrl', 'nginxTrustedProxy']

    def tuneDefaults(self):
        return {
            'minMemory': '4M',
            'connMemory': '32K',
            'connFD': 8,
            'socketTypes': ['unix', 'tcp', 'tcp6'],
            'socketType': 'unix',
            'socketProtocol': 'http',
            'scalable': False,
            'reloadable': True,
            'multiCore': True,
            'maxRequestSize': '1M',
        }

    def _installTool(self, env):
        base_url = env['nginxBaseUrl']

        if env['nginxVer'] == 'mainline':
            base_url += '/mainline'

        if self._isDebian():
            self._addAptRepo(
                'nginx',
                'deb {0}/debian/ $codename$ nginx'.format(base_url),
                self._GPG_KEY,
                codename_map={
                    'sid': 'stretch',
                    'testing': 'stretch',
                })

        elif self._isUbuntu():
            self._addAptRepo(
                'nginx',
                'deb {0}/ubuntu/ $codename$ nginx'.format(base_url),
                self._GPG_KEY,
                codename_map={
                    'zesty': 'yakkety',
                })

        elif self._isCentOS() or self._isOracleLinux():
            self._addYumRepo(
                'nginx',
                '{0}/centos/$releasever/$basearch/'.format(base_url),
                self._GPG_KEY,
                repo_url=True)

        elif self._isFedora():
            self._addYumRepo(
                'nginx',
                '{0}/centos/7/$basearch/'.format(base_url),
                self._GPG_KEY,
                repo_url=True)

        elif self._isRHEL():
            self._addYumRepo(
                'nginx',
                '{0}/rhel/$releasever/$basearch/'.format(base_url),
                self._GPG_KEY,
                repo_url=True)

        elif self._isSLES():
            self._addZypperRepo(
                'nginx',
                '{0}/sles/$releasever/$basearch/'.format(base_url),
                self._GPG_KEY,
                yum=True)

        elif self._isArchLinux():
            if env['nginxVer'] == 'mainline':
                self._requirePacman('nginx-mainline')
            else:
                self._requirePacman('nginx')
            return

        self._requirePackages('nginx')
        self._requireApk('nginx')
        self._requireBrew('nginx')

    def initEnv(self, env, bin_name=None):
        env.setdefault('nginxBaseUrl', 'http://nginx.org/packages')
        env.setdefault('nginxVer', 'stable')

        super(nginxTool, self).initEnv(env, bin_name)

        sbin_nginx = '/usr/sbin/nginx'

        if not self._have_tool and os.path.exists(sbin_nginx):
            env['nginxBin'] = sbin_nginx
            self._have_tool = True

    def onPreConfigure(self, config, runtime_dir, svc, cfg_svc_tune):
        deploy = config['deploy']

        name_id = '{0}-{1}'.format(svc['name'], svc['instanceId'])

        conf_file = 'nginx-{0}.conf'.format(name_id)
        conf_file = os.path.join(runtime_dir, conf_file)

        pid_file = 'nginx-{0}.pid'.format(name_id)
        pid_file = os.path.join(runtime_dir, pid_file)

        cfg_svc_tune['nginxConf'] = conf_file

        # max of all proxied connections
        max_request_size = self._parseMemory(svc['tune']['maxRequestSize'])
        for sl in deploy['autoServices'].values():
            for s in sl:
                max_request_size = max(
                    max_request_size,
                    self._parseMemory(s['maxRequestSize'])
                )
        cfg_svc_tune['maxRequestSize'] = self._toMemory(max_request_size)
        #
        tmp_path = os.path.join(deploy['tmpDir'], 'nginx')
        self._mkDir(tmp_path)

        #
        conf_builder = ConfigBuilder(config, svc)
        nginx_conf = conf_builder.build(name_id, pid_file, tmp_path)
        self._writeTextFile(conf_file, nginx_conf)

        # Verify
        #---
        env = config['env']
        self._callExternal([
            env['nginxBin'],
            '-q', '-t',
            '-p', runtime_dir,
            '-c', conf_file,
        ])

    def onRun(self, config, svc, args):
        env = config['env']
        deploy = config['deploy']
        self._callInteractive([
            env['nginxBin'],
            '-p', deploy['runtimeDir'],
            '-c', svc['tune']['nginxConf'],
        ] + args)

    def onStop(self, config, pid, tune):
        env = config['env']
        deploy = config['deploy']
        self._callExternal([
            env['nginxBin'],
            '-s', 'stop',
            '-p', deploy['runtimeDir'],
            '-c', tune['nginxConf'],
        ])

    def onReload(self, config, pid, tune):
        env = config['env']
        deploy = config['deploy']
        self._callExternal([
            env['nginxBin'],
            '-s', 'reload',
            '-p', deploy['runtimeDir'],
            '-c', tune['nginxConf'],
        ])
