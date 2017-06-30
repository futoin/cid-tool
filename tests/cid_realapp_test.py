
import os
import sys
import time
import signal
import stat
import pwd
import grp
import glob

import requests

from .cid_utbase import cid_UTBase
from futoin.cid.subtool import SubTool

DB_HOST = os.environ.get('DB_HOST', '10.11.1.11')

class cid_redmine_Test( cid_UTBase, SubTool ) :
    __test__ = True
    
    TEST_DIR = os.path.join(cid_UTBase.TEST_RUN_DIR, 'realapp_redmine')
    _create_test_dir = True

    def test01_deploy(self):
        self._call_cid(['deploy', 'setup'])

        self._call_cid(['deploy', 'set', 'action', 'prepare', 'app-config', 'database-config', 'app-install'])
        self._call_cid(['deploy', 'set', 'action', 'app-config',
                        'cp config/configuration.yml.example config/configuration.yml',
                        'rm -rf tmp && ln -s ../.tmp tmp'])
        self._call_cid(['deploy', 'set', 'action', 'database-config',
                        'ln -s ../../.database.yml config/database.yml'])
        self._call_cid(['deploy', 'set', 'action', 'app-install',
                        '@cid build-dep ruby mysql-client imagemagick tzdata libxml2',
                        '@cid tool exec bundler -- install --without "development test rmagick"'])
        self._call_cid(['deploy', 'set', 'action', 'migrate',
                        '@cid tool exec bundler -- exec rake generate_secret_token',
                        '@cid tool exec bundler -- exec rake db:migrate RAILS_ENV=production',
                        '@cid tool exec bundler -- exec rake redmine:load_default_data RAILS_ENV=production REDMINE_LANG=en',])
        
        self._call_cid(['deploy', 'set', 'persistent', 'files', 'log', 'public/plugin_assets'])
        
        self._call_cid(['deploy', 'set', 'env', 'rubyVer', '2.3'])
        
        self._call_cid(['deploy', 'set', 'entrypoint', 'web', 'nginx', 'public', 'socketPort=1234'])
        self._call_cid(['deploy', 'set', 'entrypoint', 'app', 'puma', 'config.ru', 'internal=1'])
        
        self._call_cid(['deploy', 'set', 'webcfg', 'main', 'app'])
        
        self._writeFile('.database.yml', """
production:
  adapter: mysql2
  database: redmine
  host: {0}
  username: redmine
  password: redmine
  encoding: utf8
""".format(DB_HOST))
        
        if self._isAlpineLinux() or self._isArchLinux():
            # Ruby 2.4
            self._call_cid([
                'deploy', 'vcsref', 'trunk',
                '--vcsRepo=svn:http://svn.redmine.org/redmine'
                ])
        else:
            self._call_cid([
                'deploy', 'vcstag',
                '--vcsRepo=svn:http://svn.redmine.org/redmine'
                ])
            
        self._writeFile(os.path.join('persistent', 'public', 'plugin_assets', 'file.txt'), 'STATICFILE')
    
    def test02_execute(self):
        pid = os.fork()
        
        if not pid:
            self._redirectAsyncStdIO()
            os.execv(self.CIDTEST_BIN, [self.CIDTEST_BIN, 'service', 'master'])
        
        try:
            res = self._firstGet('http://127.0.0.1:1234/plugin_assets/file.txt')
            self.assertEqual('STATICFILE', res.strip())
            
            res = self._firstGet('http://127.0.0.1:1234/')
            
            if res.find('redmine') < 0:
                print(res)
                self.assertFalse(True)
                
        finally:
            os.kill(pid, signal.SIGTERM)
            try: os.waitpid(pid, 0)
            except OSError: pass
        