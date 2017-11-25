#
# Copyright 2015-2017 Andrey Galkin <andrey@futoin.org>
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

import os
import sys
import time
import signal
import stat
import pwd
import grp
import glob

import requests
from nose.plugins.attrib import attr

from .cid_utbase import cid_UTBase
from futoin.cid.mixins.ondemand import ext

DB_HOST = os.environ.get('DB_HOST', '10.11.1.11')

@attr(tool='ruby')
class cid_redmine_Test( cid_UTBase ) :
    __test__ = True
    
    TEST_DIR = os.path.join(cid_UTBase.TEST_RUN_DIR, 'realapp_redmine')
    _create_test_dir = True

    def test01_deploy(self):
        self._call_cid(['deploy', 'setup'])
        
        if ext.detect.isAlpineLinux() or ext.detect.isArchLinux():
            self._call_cid(['deploy', 'set', 'env', 'rubyVer', 'system'])
            db = 'redmine_trunk'
        else:
            self._call_cid(['deploy', 'set', 'env', 'rubyVer', '2.3'])
            db = 'redmine'

        self._call_cid(['deploy', 'set', 'action', 'prepare', 'app-config', 'database-config', 'app-install'])
        self._call_cid(['deploy', 'set', 'action', 'app-config',
                        'cp config/configuration.yml.example config/configuration.yml',
                        'rm -rf tmp && ln -s ../.tmp tmp'])
        self._call_cid(['deploy', 'set', 'action', 'database-config',
                        'ln -s ../../.database.yml config/database.yml'])
        self._call_cid(['deploy', 'set', 'action', 'app-install',
                        '@cid build-dep ruby mysql-client imagemagick tzdata libxml2',
                        #'env',
                        #'@cid tool env bundler',
                        "@cid tool exec gem -- env",
                        '@cid tool exec bundler -- install --without "development test rmagick"'])
        self._call_cid(['deploy', 'set', 'action', 'migrate',
                        '@cid tool exec bundler -- exec rake generate_secret_token',
                        '@cid tool exec bundler -- exec rake db:migrate RAILS_ENV=production',
                        '@cid tool exec bundler -- exec rake redmine:load_default_data RAILS_ENV=production REDMINE_LANG=en',])
        
        self._call_cid(['deploy', 'set', 'persistent', 'files', 'log', 'public/plugin_assets'])
        
        self._call_cid(['deploy', 'set', 'entrypoint', 'web', 'nginx', 'public', 'socketType=tcp', 'socketPort=1234'])
        self._call_cid(['deploy', 'set', 'entrypoint', 'app', 'puma', 'config.ru', 'internal=1'])
        
        self._call_cid(['deploy', 'set', 'webcfg', 'root', 'public'])
        self._call_cid(['deploy', 'set', 'webcfg', 'main', 'app'])
        self._call_cid(['deploy', 'set', 'webmount', '/', '{"static": true}'])
        
        self._writeFile('.database.yml', """
production:
  adapter: mysql2
  database: {1}
  host: {0}
  username: redmine
  password: redmine
  encoding: utf8
""".format(DB_HOST, db))
        
        if ext.detect.isAlpineLinux() or ext.detect.isArchLinux():
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
            self.assertEqual('STATICFILE', res.text.strip())
            
            res = self._firstGet('http://127.0.0.1:1234/')
            
            if res.text.find('redmine') < 0:
                print(res)
                self.assertFalse(True)
                
        finally:
            os.kill(pid, signal.SIGTERM)
            try: os.waitpid(pid, 0)
            except OSError: pass

@attr(tool='php')
class cid_nextcloud_Test( cid_UTBase ) :
    __test__ = True
    
    TEST_DIR = os.path.join(cid_UTBase.TEST_RUN_DIR, 'realapp_nextcloud')
    _create_test_dir = True

    def test01_deploy(self):
        self._call_cid(['deploy', 'setup'])
        
        exts = [
            'ctype',
            'dom',
            'gd',
            'iconv',
            'json',
            'xml',
            'mbstring',
            'posix',
            'simplexml',
            'xmlreader',
            'xmlwriter',
            'zip',
            'zlib',
            'pdo_mysql',
            'curl',
            'fileinfo',
            'bz2',
            'intl',
            'mcrypt',
            'openssl',
            'ldap',
            'ftp',
            'imap',
            'exif',
            'gmp',
            'apcu',
            'imagick',
        ]
        
        self._call_cid(['deploy', 'set', 'env', 'phpExtRequire', ' '.join(exts)])

    def test02_execute(self):
        return # TODO:
        pid = os.fork()
        
        if not pid:
            self._redirectAsyncStdIO()
            os.execv(self.CIDTEST_BIN, [self.CIDTEST_BIN, 'service', 'master'])
        
        try:
            res = self._firstGet('http://127.0.0.1:1234/plugin_assets/file.txt')
            self.assertEqual('STATICFILE', res.text.strip())
            
            res = self._firstGet('http://127.0.0.1:1234/')
            
            if res.text.find('redmine') < 0:
                print(res)
                self.assertFalse(True)
                
        finally:
            os.kill(pid, signal.SIGTERM)
            try: os.waitpid(pid, 0)
            except OSError: pass
        
