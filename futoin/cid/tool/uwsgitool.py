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
from .piptoolmixin import PipToolMixIn


class uwsgiTool(PipToolMixIn, RuntimeTool):
    """uWSGI application server container http://projects.unbit.it/uwsgi

Currently, used for Python WSGI apps.

It's possible to override uWSGI options with .tune.uwsgi parameter map.
"""
    __slots__ = ()

    def tuneDefaults(self, env):
        return {
            'internal': True,
            'minMemory': '64M',
            'connMemory': '16M',
            'debugConnOverhead': '4M',
            'connFD': 8,
            'socketTypes': ['unix', 'tcp', 'tcp6'],
            'socketType': 'unix',
            'socketProtocol': 'uwsgi',
            'scalable': True,
            'reloadable': False,  # there are too many gotchas for graceful reload
            'multiCore': False,  # make there is no uWSGI master bottleneck
            'maxRequestSize': '1M',
        }

    def onPreConfigure(self, config, runtime_dir, svc, cfg_svc_tune):
        ospath = self._ospath
        configutil = self._configutil
        env = config['env']
        deploy = config['deploy']

        name_id = '{0}-{1}'.format(svc['name'], svc['instanceId'])
        svc_tune = svc['tune']

        conf_file = 'uwsgi-{0}.ini'.format(name_id)
        conf_file = ospath.join(runtime_dir, conf_file)

        pid_file = 'uwsgi-{0}.pid'.format(name_id)
        pid_file = ospath.join(runtime_dir, pid_file)

        target_cwd = config['wcDir']

        cfg_svc_tune['uwsgiConf'] = conf_file
        cfg_svc_tune['uwsgiPid'] = pid_file

        #
        socket_type = svc_tune['socketType']

        if socket_type == 'unix':
            socket = svc_tune['socketPath']
        elif socket_type == 'tcp':
            socket = '{0}:{1}'.format(
                svc_tune['socketAddress'], svc_tune['socketPort'])
        else:
            self._errorExit(
                'Unsupported socket type "{0}" for "{1}"'.format(socket_type, name_id))

        # Most of RSS is assumed to be shared with
        # uWSGI master process through CoW. So, each workes RSS
        # is minMemory=master + connMemory=worker_overhead.
        mem_limit = configutil.parseMemory(svc_tune['minMemory'])
        mem_limit += configutil.parseMemory(svc_tune['connMemory'])
        mem_limit = int(mem_limit / 1024 / 1024)
        conf = {
            'uwsgi': svc_tune.get('uwsgi', {})
        }

        uwsgi_conf = conf['uwsgi']

        uwsgi_conf.update({
            'uwsgi-socket': socket,
            'master': 1,
            'workers': svc_tune['maxConnections'],
            'strict': 1,
            'virtualenv': env['virtualenvDir'],
            'single-interpreter': 1,
            'reload-on-rss': mem_limit,
            'evil-reload-on-rss': mem_limit * 2,
            'never-swap': 1,
            'need-app': 1,
            'reaper': 1,
            'logger': 'syslog:{0}'.format(configutil.syslogTag(env, name_id)),
            'disable-logging': 1,
            'die-on-term': 1,
            'chdir': target_cwd,
            'hook-post-fork': 'chdir:{0}'.format(target_cwd),
        })

        uwsgi_conf.setdefault('max-requests', 5000)
        uwsgi_conf.setdefault('harakiri', 20)
        uwsgi_conf.setdefault('vacuum', True)

        if svc['path']:
            uwsgi_conf['wsgi-file'] = svc['path']

        self._pathutil.writeIni(conf_file, conf)

    def onRun(self, config, svc, args):
        env = config['env']
        deploy = config['deploy']
        self._executil.callInteractive([
            env['uwsgiBin'],
            svc['tune']['uwsgiConf']
        ])
