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
* .upstreamZoneSize = 64k - shared memory for upstream zones
* .upstreamFailTimeout = 10 - upstream failure timeout
* .upstreamQueue = None - paramaters to "queue", if set (commercial)
* .upstreamKAPercent = 25 - Keep-Alive percent
* .proxyProtocol = False - enable binary proxy-protocol



Additional notes:
* proxy buffering is disabled and assumed to be part of front- or middle- balancers

"""
    __slots__ = ()

    _GPG_KEY = GPG_KEY

    def envNames(self):
        return ['nginxBin', 'nginxVer', 'nginxBaseUrl', 'nginxTrustedProxy']

    def tuneDefaults(self, env):
        return {
            'minMemory': '4M',
            'connMemory': '32K',
            'connFD': 8,
            'socketTypes': ['unix', 'tcp', 'tcp6'],
            'socketType': 'tcp' if env['type'] == 'dev' else 'unix',
            'socketProtocol': 'http',
            'scalable': False,
            'reloadable': True,
            'multiCore': True,
            'maxRequestSize': '1M',
            'memoryWeight': 10,
        }

    def _installTool(self, env):
        base_url = env['nginxBaseUrl']

        if env['nginxVer'] == 'mainline':
            base_url += '/mainline'

        detect = self._detect

        if detect.isDebian():
            self._install.aptRepo(
                'nginx',
                'deb {0}/debian/ $codename$ nginx'.format(base_url),
                self._GPG_KEY,
                codename_map={
                    'sid': 'stretch',
                    'testing': 'stretch',
                })

        elif detect.isUbuntu():
            self._install.aptRepo(
                'nginx',
                'deb {0}/ubuntu/ $codename$ nginx'.format(base_url),
                self._GPG_KEY,
                codename_map={})

        elif detect.isCentOS():
            dist_ver = self._detect.linuxDistMajorVer()

            self._install.yumRepo(
                'nginx',
                '{0}/centos/{1}/$basearch/'.format(base_url, dist_ver),
                self._GPG_KEY,
                repo_url=True)

        elif detect.isFedora():
            self._install.yumRepo(
                'nginx',
                '{0}/centos/7/$basearch/'.format(base_url),
                self._GPG_KEY,
                repo_url=True)

        elif detect.isRHEL() or detect.isOracleLinux():
            dist_ver = self._detect.linuxDistMajorVer()

            self._install.yumRepo(
                'nginx',
                '{0}/rhel/{1}/$basearch/'.format(base_url, dist_ver),
                self._GPG_KEY,
                repo_url=True)

        elif detect.isSLES():
            sles_ver = self._detect.linuxDistMajorVer()
            self._install.zypperRepo(
                'nginx',
                '{0}/sles/{1}/'.format(base_url, sles_ver),
                self._GPG_KEY,
                yum=True)

        elif detect.isArchLinux():
            if env['nginxVer'] == 'mainline':
                self._install.pacman('nginx-mainline')
            else:
                self._install.pacman('nginx')
            return

        self._install.debrpm('nginx')
        self._install.apk('nginx')
        self._install.brew('nginx')

    def initEnv(self, env, bin_name=None):
        env.setdefault('nginxBaseUrl', 'http://nginx.org/packages')
        env.setdefault('nginxVer', 'stable')

        super(nginxTool, self).initEnv(env, bin_name)

        sbin_nginx = '/usr/sbin/nginx'

        if not self._have_tool and self._ospath.exists(sbin_nginx):
            env['nginxBin'] = sbin_nginx
            self._have_tool = True

    def onPreConfigure(self, config, runtime_dir, svc, cfg_svc_tune):
        ospath = self._ospath
        deploy = config['deploy']

        name_id = '{0}-{1}'.format(svc['name'], svc['instanceId'])

        conf_file = 'nginx-{0}.conf'.format(name_id)
        conf_file = ospath.join(runtime_dir, conf_file)

        pid_file = 'nginx-{0}.pid'.format(name_id)
        pid_file = ospath.join(runtime_dir, pid_file)

        cfg_svc_tune['nginxConf'] = conf_file

        # max of all proxied connections
        max_request_size = self._configutil.parseMemory(
            svc['tune']['maxRequestSize'])
        for sl in deploy['autoServices'].values():
            for s in sl:
                max_request_size = max(
                    max_request_size,
                    self._configutil.parseMemory(s['maxRequestSize'])
                )
        cfg_svc_tune['maxRequestSize'] = self._configutil.toMemory(
            max_request_size)
        #
        tmp_path = ospath.join(deploy['tmpDir'], 'nginx')
        self._pathutil.mkDir(tmp_path)

        #
        conf_builder = ConfigBuilder(config, svc)
        nginx_conf = conf_builder.build(name_id, pid_file, tmp_path)
        self._pathutil.writeTextFile(conf_file, nginx_conf)

        # Verify
        # ---
        env = config['env']
        self._executil.callExternal([
            env['nginxBin'],
            '-q', '-t',
            '-p', runtime_dir,
            '-c', conf_file,
        ])

    def onRun(self, config, svc, args):
        env = config['env']
        deploy = config['deploy']
        self._executil.callInteractive([
            env['nginxBin'],
            '-p', deploy['runtimeDir'],
            '-c', svc['tune']['nginxConf'],
        ] + args)

    def onStop(self, config, pid, tune):
        env = config['env']
        deploy = config['deploy']
        self._executil.callExternal([
            env['nginxBin'],
            '-s', 'stop',
            '-p', deploy['runtimeDir'],
            '-c', tune['nginxConf'],
        ])

    def onReload(self, config, pid, tune):
        env = config['env']
        deploy = config['deploy']
        self._executil.callExternal([
            env['nginxBin'],
            '-s', 'reload',
            '-p', deploy['runtimeDir'],
            '-c', tune['nginxConf'],
        ])
