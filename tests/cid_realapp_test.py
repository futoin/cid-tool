
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

        self._call_cid(['deploy', 'set-action', 'prepare', 'app-config', 'database-config', 'app-install'])
        self._call_cid(['deploy', 'set-action', 'app-config',
                        'cp config/configuration.yml.example config/configuration.yml',
                        'rm tmp -rf && ln -s ../.tmp tmp'])
        self._call_cid(['deploy', 'set-action', 'database-config',
                        'ln -s ../../.database.yml config/database.yml'])
        self._call_cid(['deploy', 'set-action', 'app-install',
                        '@cid tool exec bundler -- install --without development test'])
        self._call_cid(['deploy', 'set-action', 'migrate',
                        '@cid tool exec bundler -- bundle exec rake generate_secret_token',
                        '@cid tool exec bundler -- bundle exec rake db:migrate RAILS_ENV=production',
                        '@cid tool exec bundler -- bundle exec rake redmine:load_default_data RAILS_ENV=production REDMINE_LANG=en',])
        self._call_cid(['deploy', 'set-persistent', 'files', 'log', 'public/plugin_assets'])
        
        self._writeFile('.database.yml', """
production:
  adapter: mysql2
  database: redmine
  host: {0}
  username: redmine
  password: redmine
  encoding: utf8
""".format(DB_HOST))
        
        self._call_cid([
            'deploy', 'vcstag',
            '--vcsRepo=svn:http://svn.redmine.org/redmine'
            ])
    
    def test02_execute(self):
        pass