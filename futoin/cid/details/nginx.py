
import os
import copy
from collections import OrderedDict

from ..mixins.util import UtilMixIn
from ..mixins.path import PathMixIn
from ..mixins.package import PackageMixIn


GPG_KEY = """
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v2.0.22 (GNU/Linux)

mQENBE5OMmIBCAD+FPYKGriGGf7NqwKfWC83cBV01gabgVWQmZbMcFzeW+hMsgxH
W6iimD0RsfZ9oEbfJCPG0CRSZ7ppq5pKamYs2+EJ8Q2ysOFHHwpGrA2C8zyNAs4I
QxnZZIbETgcSwFtDun0XiqPwPZgyuXVm9PAbLZRbfBzm8wR/3SWygqZBBLdQk5TE
fDR+Eny/M1RVR4xClECONF9UBB2ejFdI1LD45APbP2hsN/piFByU1t7yK2gpFyRt
97WzGHn9MV5/TL7AmRPM4pcr3JacmtCnxXeCZ8nLqedoSuHFuhwyDnlAbu8I16O5
XRrfzhrHRJFM1JnIiGmzZi6zBvH0ItfyX6ttABEBAAG0KW5naW54IHNpZ25pbmcg
a2V5IDxzaWduaW5nLWtleUBuZ2lueC5jb20+iQE+BBMBAgAoAhsDBgsJCAcDAgYV
CAIJCgsEFgIDAQIeAQIXgAUCV2K1+AUJGB4fQQAKCRCr9b2Ce9m/YloaB/9XGrol
kocm7l/tsVjaBQCteXKuwsm4XhCuAQ6YAwA1L1UheGOG/aa2xJvrXE8X32tgcTjr
KoYoXWcdxaFjlXGTt6jV85qRguUzvMOxxSEM2Dn115etN9piPl0Zz+4rkx8+2vJG
F+eMlruPXg/zd88NvyLq5gGHEsFRBMVufYmHtNfcp4okC1klWiRIRSdp4QY1wdrN
1O+/oCTl8Bzy6hcHjLIq3aoumcLxMjtBoclc/5OTioLDwSDfVx7rWyfRhcBzVbwD
oe/PD08AoAA6fxXvWjSxy+dGhEaXoTHjkCbz/l6NxrK3JFyauDgU4K4MytsZ1HDi
MgMW8hZXxszoICTTiQEcBBABAgAGBQJOTkelAAoJEKZP1bF62zmo79oH/1XDb29S
YtWp+MTJTPFEwlWRiyRuDXy3wBd/BpwBRIWfWzMs1gnCjNjk0EVBVGa2grvy9Jtx
JKMd6l/PWXVucSt+U/+GO8rBkw14SdhqxaS2l14v6gyMeUrSbY3XfToGfwHC4sa/
Thn8X4jFaQ2XN5dAIzJGU1s5JA0tjEzUwCnmrKmyMlXZaoQVrmORGjCuH0I0aAFk
RS0UtnB9HPpxhGVbs24xXZQnZDNbUQeulFxS4uP3OLDBAeCHl+v4t/uotIad8v6J
SO93vc1evIje6lguE81HHmJn9noxPItvOvSMb2yPsE8mH4cJHRTFNSEhPW6ghmlf
Wa9ZwiVX5igxcvaIRgQQEQIABgUCTk5b0gAKCRDs8OkLLBcgg1G+AKCnacLb/+W6
cflirUIExgZdUJqoogCeNPVwXiHEIVqithAM1pdY/gcaQZmIRgQQEQIABgUCTk5f
YQAKCRCpN2E5pSTFPnNWAJ9gUozyiS+9jf2rJvqmJSeWuCgVRwCcCUFhXRCpQO2Y
Va3l3WuB+rgKjsQ=
=EWWI
-----END PGP PUBLIC KEY BLOCK-----

"""

FASTCGI_PARAMS = """
fastcgi_param  QUERY_STRING       $query_string;
fastcgi_param  REQUEST_METHOD     $request_method;
fastcgi_param  CONTENT_TYPE       $content_type;
fastcgi_param  CONTENT_LENGTH     $content_length;

fastcgi_param  SCRIPT_NAME        $fastcgi_script_name;
fastcgi_param  REQUEST_URI        $request_uri;
fastcgi_param  DOCUMENT_URI       $document_uri;
fastcgi_param  DOCUMENT_ROOT      $document_root;
fastcgi_param  SERVER_PROTOCOL    $server_protocol;
fastcgi_param  REQUEST_SCHEME     $scheme;
fastcgi_param  HTTPS              $https if_not_empty;

fastcgi_param  GATEWAY_INTERFACE  CGI/1.1;
fastcgi_param  SERVER_SOFTWARE    nginx/$nginx_version;

fastcgi_param  SERVER_ADDR        $server_addr;
fastcgi_param  SERVER_PORT        $server_port;
fastcgi_param  SERVER_NAME        $server_name;

# PHP only, required if PHP was built with --enable-force-cgi-redirect
fastcgi_param  REDIRECT_STATUS    200;
"""

SCGI_PARAMS = """
scgi_param  REQUEST_METHOD     $request_method;
scgi_param  REQUEST_URI        $request_uri;
scgi_param  QUERY_STRING       $query_string;
scgi_param  CONTENT_TYPE       $content_type;

scgi_param  DOCUMENT_URI       $document_uri;
scgi_param  DOCUMENT_ROOT      $document_root;
scgi_param  SCGI               1;
scgi_param  SERVER_PROTOCOL    $server_protocol;
scgi_param  REQUEST_SCHEME     $scheme;
scgi_param  HTTPS              $https if_not_empty;

scgi_param  SERVER_PORT        $server_port;
scgi_param  SERVER_NAME        $server_name;
"""

UWSGI_PARAMS = """
uwsgi_param  QUERY_STRING       $query_string;
uwsgi_param  REQUEST_METHOD     $request_method;
uwsgi_param  CONTENT_TYPE       $content_type;
uwsgi_param  CONTENT_LENGTH     $content_length;

uwsgi_param  REQUEST_URI        $request_uri;
uwsgi_param  PATH_INFO          $document_uri;
uwsgi_param  DOCUMENT_ROOT      $document_root;
uwsgi_param  SERVER_PROTOCOL    $server_protocol;
uwsgi_param  REQUEST_SCHEME     $scheme;
uwsgi_param  HTTPS              $https if_not_empty;

uwsgi_param  SERVER_PORT        $server_port;
uwsgi_param  SERVER_NAME        $server_name;
"""


class ConfigBuilder(UtilMixIn, PathMixIn, PackageMixIn):
    def __init__(self, config, svc):
        self._config = config
        self._nginx_conf = copy.deepcopy(svc['tune'].get('config', {}))
        self._svc = svc
        self._remote_addr_var = '$remote_addr'
        self._remote_port_var = '$remote_port'
        self._x_forwarded_for_var = '$proxy_add_x_forwarded_for'

        env = config['env']
        nginx_bin = env['nginxBin']

        #---
        if self._isMacOS():
            brew_dir = env.get('brewDir', '')

            if brew_dir:
                self._prefix = brew_dir
            else:
                self._prefix = '/usr/local'
        else:
            self._prefix = ''

        #---
        ver = self._callExternal(
            [nginx_bin, '-v'],
            verbose=False, merge_stderr=True)
        ver = ver.split('/')[1].strip().split('.')
        ver = [int(v) for v in ver]
        self._version = tuple(ver)

    def build(self, name_id, pid_file, tmp_path):
        config = self._config
        deploy = config['deploy']
        svc = self._svc
        svc_tune = svc['tune']
        conf = self._nginx_conf
        cid_tune = svc_tune.get('cid', {})

        # Global
        #---
        #conf['user'] = '{0} {1}'.format(deploy['user'], deploy['group'])
        conf['worker_processes'] = svc_tune['maxCpuCount']
        conf.setdefault('error_log', 'stderr error')
        conf['worker_rlimit_nofile'] = svc_tune['maxFD']
        conf['daemon'] = 'off'
        conf['pcre_jit'] = 'on'
        conf['working_directory'] = config['deployDir']
        conf['timer_resolution'] = '10ms'
        conf['pid'] = pid_file

        # Events
        #---
        events = conf.setdefault('events', OrderedDict())
        events['worker_connections'] = int(
            svc_tune['maxFD'] // svc_tune['maxCpuCount'])

        # HTTP
        #---
        http = conf.setdefault('http', OrderedDict())
        http.setdefault(
            '-types', "include {0}/etc/nginx/mime.types;".format(self._prefix))
        http.setdefault('default_type', 'application/octet-stream')
        http.setdefault('access_log', 'off')
        http.setdefault('log_not_found', 'off')

        #
        temp_path_opt = http.setdefault(
            'client_body_temp_path', '{0} 1 2'.format(tmp_path))
        http.setdefault('proxy_temp_path', temp_path_opt)
        http.setdefault('fastcgi_temp_path', temp_path_opt)
        http.setdefault('uwsgi_temp_path', temp_path_opt)
        http.setdefault('scgi_temp_path', temp_path_opt)
        #
        http.setdefault('proxy_buffering', 'off')
        http.setdefault('proxy_request_buffering', 'off')
        http.setdefault('proxy_max_temp_file_size', '0')
        http.setdefault('proxy_next_upstream', 'error')
        #
        http.setdefault('fastcgi_buffering', 'off')
        http.setdefault('fastcgi_request_buffering', 'off')
        http.setdefault('fastcgi_max_temp_file_size', '0')
        http.setdefault('fastcgi_next_upstream', 'error')
        #
        if not self._isMacOS():
            http.setdefault('aio', 'threads')
            if self._version >= (1, 9, 13):
                http.setdefault('aio_write', 'on')
        #
        http.setdefault('server_tokens', 'off')

        http['map $http_upgrade $connection_upgrade'] = {
            'default': 'upgrade',
            "''": "''",
        }

        # The only vhost
        #---
        server = http.setdefault('server', OrderedDict())
        server['root'] = os.path.join(config['wcDir'], svc['path'])
        server.setdefault('gzip_static', 'on')
        server.setdefault('server_name', '_')

        socket_type = svc_tune['socketType']

        if socket_type == 'unix':
            listen = 'unix:{0}'.format(svc_tune['socketPath'])
            server['set_real_ip_from'] = 'unix:'

        elif socket_type == 'tcp':
            listen = '{0}:{1}'.format(
                svc_tune['socketAddress'], svc_tune['socketPort'])
        elif socket_type == 'tcp6':
            listen = '[{0}]:{1}'.format(
                svc_tune['socketAddress'], svc_tune['socketPort'])
        else:
            self._errorExit(
                'Unsupported socket type "{0}" for "{1}"'.format(socket_type, name_id))

        listen += ' '
        listenOptions = 'default_server'

        if self._isLinux():
            listenOptions += ' deferred'

        listen += cid_tune.get('listenOptions', listenOptions)

        if cid_tune.get('proxyProtocol', False):
            listen += ' proxy_protocol'
            server['real_ip_header'] = 'proxy_protocol'

            if socket_type != 'unix':
                trusted = config['env'].get('nginxTrustedProxy', '0.0.0.0/0')
                server['set_real_ip_from'] = trusted.split()

        server['listen'] = listen

        # Location per each webapp
        #---
        webcfg = config.get('webcfg', {})
        mounts = webcfg.get('mounts', {}).copy()
        autoServices = deploy['autoServices']
        main = webcfg.get('main', None)

        if main:
            mounts['/'] = main

        for (prefix, app) in mounts.items():
            try:
                instances = autoServices[app]
                appsvc = config['entryPoints'][app]
            except KeyError:
                self._errorExit(
                    'Missing "autoServices" for "{0}" entry point'.format(app))

            try:
                protocol = instances[0]['socketProtocol']
            except KeyError:
                self._errorExit(
                    'Missing "socketProtocol" for "{0}" entry point'.format(app))

            if protocol == 'http':
                upstream, location = self._proxyHttp(app, appsvc, instances)
            elif protocol == 'fcgi':
                upstream, location = self._proxyFcgi(app, appsvc, instances)
            elif protocol == 'scgi':
                upstream, location = self._proxyScgi(app, appsvc, instances)
            elif protocol == 'uwsgi':
                upstream, location = self._proxyUwsgi(app, appsvc, instances)
            else:
                self._errorExit(
                    'Not supported protocol "{0}" for "{1}" entry point'.format(protocol, app))

            http['upstream {0}'.format(app)] = upstream

            if prefix == '/' and cid_tune.get('serveStatic', True):
                server['location @main'] = location
                server['location /'] = {
                    'try_files': '$uri @main',
                    'disable_symlinks': 'if_not_owner from={0}'.format(server['root']),
                }
            else:
                server['location {0}'.format(prefix)] = location

        return self.getTextConfig()

    def _upstreamCommon(self, app, svc, instances, keepalive=False):
        svc_tune = svc['tune']
        cid_tune = svc_tune.get('cid', {})
        zone_size = cid_tune.get('upstreamZoneSize', '64k')
        file_timeout = cid_tune.get('upstreamFailTimeout', '10')
        keep_alive_percent = cid_tune.get('upstreamKAPercent', 25)
        queue = cid_tune.get('upstreamQueue', None)

        upstream = OrderedDict()

        if self._version >= (1, 9, 0):
            upstream['zone'] = 'upstreams {0}'.format(zone_size)
            upstream['hash'] = '$binary_remote_addr consistent'

        if queue:
            upstream['queue'] = queue

        if keepalive and keep_alive_percent > 0:
            ka_conn = 0
            for v in instances:
                ka_conn += v['maxConnections']
            ka_conn = int(ka_conn * keep_alive_percent // 100)

            if ka_conn:
                upstream['keepalive'] = ka_conn

        for v in instances:
            options = []
            if self._version >= (1, 9, 0):
                options.append('max_conns={0}'.format(v['maxConnections']))

            options.append('max_fails=0')
            options.append('fail_timeout={0}'.format(file_timeout))

            socket_type = v['socketType']

            if socket_type == 'unix':
                socket = 'unix:{0}'.format(v['socketPath'])
            elif socket_type == 'tcp':
                sock_addr = v['socketAddress']

                if sock_addr == '0.0.0.0':
                    sock_addr = '127.0.0.1'

                socket = '{0}:{1}'.format(sock_addr, v['socketPort'])
            elif socket_type == 'tcp6':
                sock_addr = v['socketAddress']

                if sock_addr == '::':
                    sock_addr = '::1'

                socket = '[{0}]:{1}'.format(sock_addr, v['socketPort'])
            else:
                self._errorExit(
                    'Unsupported socket type "{0}" for "{1}"'.format(socket_type, app))

            upstream['server {0}'.format(socket)] = ' '.join(options)

        return upstream

    def _svcBodyLimit(self, instances):
        return self._parseMemory(instances[0]['maxRequestSize'])

    def _proxyHttp(self, app, svc, instances):
        upstream = self._upstreamCommon(app, svc, instances, True)
        location = OrderedDict()
        location['proxy_pass'] = 'http://{0}'.format(app)
        location['proxy_http_version'] = '1.1'
        location['proxy_set_header Upgrade'] = '$http_upgrade'
        location['proxy_set_header Connection'] = '$connection_upgrade'
        location['proxy_set_header Host'] = '$host'
        location['proxy_set_header X-Real-IP'] = self._remote_addr_var
        location['proxy_set_header X-Forwarded-For'] = self._x_forwarded_for_var
        location['proxy_next_upstream_tries'] = len(instances)
        location['client_max_body_size'] = self._svcBodyLimit(instances)

        return upstream, location

    def _proxyFcgi(self, app, svc, instances):
        upstream = self._upstreamCommon(app, svc, instances, True)
        location = OrderedDict()
        location['fastcgi_pass'] = app
        location['fastcgi_keep_conn'] = 'on'
        location['fastcgi_next_upstream_tries'] = len(instances)
        location['client_max_body_size'] = self._svcBodyLimit(instances)

        location['-fastcgi-params'] = FASTCGI_PARAMS
        location['fastcgi_param REMOTE_ADDR'] = self._remote_addr_var
        location['fastcgi_param REMOTE_PORT'] = self._remote_port_var
        location['fastcgi_param SCRIPT_FILENAME'] = os.path.join(
            self._config['deployDir'], 'current', svc['path'])

        return upstream, location

    def _proxyScgi(self, app, svc, instances):
        upstream = self._upstreamCommon(app, svc, instances)
        location = OrderedDict()
        location['scgi_pass'] = app
        location['client_max_body_size'] = self._svcBodyLimit(instances)

        location['-fastcgi-params'] = SCGI_PARAMS
        location['scgi_param REMOTE_ADDR'] = self._remote_addr_var
        location['scgi_param REMOTE_PORT'] = self._remote_port_var

        return upstream, location

    def _proxyUwsgi(self, app, svc, instances):
        upstream = self._upstreamCommon(app, svc, instances)
        location = OrderedDict()
        location['uwsgi_pass'] = app
        location['client_max_body_size'] = self._svcBodyLimit(instances)

        location['-fastcgi-params'] = UWSGI_PARAMS
        location['uwsgi_param REMOTE_ADDR'] = self._remote_addr_var
        location['uwsgi_param REMOTE_PORT'] = self._remote_port_var

        return upstream, location

    def getTextConfig(self):
        def prep_config(section, prefix):
            content = []

            options = filter(lambda x: not isinstance(
                x[1], dict), section.items())
            sections = filter(lambda x: isinstance(
                x[1], dict), section.items())

            for (k, v) in options:
                if k[0] == '-':
                    v = v.split("\n")
                    v = ['{0}{1}'.format(prefix, x) for x in v]
                    v = "\n".join(v)
                    content.append(v)
                elif isinstance(v, list):
                    for lv in v:
                        content.append('{0}{1} {2};'.format(prefix, k, lv))
                else:
                    content.append('{0}{1} {2};'.format(prefix, k, v))

            for (k, v) in sections:
                content.append('')
                v = prep_config(v, prefix + "\t")
                content.append("{0}{1} {{\n{2}\n{0}}}".format(prefix, k, v))

            return "\n".join(content)

        return prep_config(self._nginx_conf, "")
