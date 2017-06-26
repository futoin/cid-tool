
import os

from ..runtimetool import RuntimeTool
from .piptoolmixin import PipToolMixIn


class uwsgiTool(PipToolMixIn, RuntimeTool):
    """uWSGI application server container http://projects.unbit.it/uwsgi

Currently, used for Python WSGI apps.

It's possible to override uWSGI options with .tune.uwsgi parameter map.
"""

    def tuneDefaults(self):
        return {
            'minMemory': '1M',
            'connMemory': '12M',
            'debugConnOverhead': '4M',
            'connFD': 8,
            'socketTypes': ['unix', 'tcp', 'tcp6'],
            'socketType': 'unix',
            'socketProtocol': 'uwsgi',
            'scalable': True,
            'reloadable': True,
            'multiCore': False,  # make there is no uWSGI master bottleneck
            'maxRequestSize': '1M',
        }

    def onPreConfigure(self, config, runtime_dir, svc, cfg_svc_tune):
        env = config['env']
        deploy = config['deploy']

        name_id = '{0}-{1}'.format(svc['name'], svc['instanceId'])

        conf_file = 'uwsgi-{0}.ini'.format(name_id)
        conf_file = os.path.join(runtime_dir, conf_file)

        pid_file = 'uwsgi-{0}.pid'.format(name_id)
        pid_file = os.path.join(runtime_dir, pid_file)

        cfg_svc_tune['uwsgiConf'] = conf_file
        cfg_svc_tune['uwsgiPid'] = pid_file

        #
        if cfg_svc_tune['socketType'] == 'unix':
            socket = cfg_svc_tune['socketPath']
        else:
            socket = '{0}:{1}'.format(
                cfg_svc_tune['socketAddress'], cfg_svc_tune['socketPort'])

        #
        mem_limit = int(self._parseMemory(
            cfg_svc_tune['connMemory']) / 1024 / 1024)
        conf = {
            'uwsgi': cfg_svc_tune.get('uwsgi', {})
        }

        uwsgi_conf = conf['uwsgi']

        uwsgi_conf.update({
            'uwsgi-socket': socket,
            'master': 1,
            'workers': cfg_svc_tune['maxConnections'],
            'strict': 1,
            'virtualenv': env['virtualenvDir'],
            'single-interpreter': 1,
            'reload-on-rss': mem_limit,
            'evil-reload-on-rss': mem_limit,
            'never-swap': 1,
            'need-app': 1,
            'reaper': 1,
            'logger': 'syslog:{0}'.format(name_id),
            'disable-logging': 1,
            'die-on-term': 1,
        })

        uwsgi_conf.setdefault('max-requests', 5000)
        uwsgi_conf.setdefault('harakiri', 20)
        uwsgi_conf.setdefault('vacuum', True)

        if svc['path']:
            uwsgi_conf['wsgi-file'] = svc['path']

        self._writeIni(conf_file, conf)

    def onRun(self, config, svc, args):
        env = config['env']
        deploy = config['deploy']
        self._callInteractive([
            env['uwsgiBin'],
            svc['tune']['uwsgiConf']
        ])
