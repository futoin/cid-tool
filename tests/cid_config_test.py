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

from __future__ import print_function, absolute_import
from nose.plugins.attrib import attr

from .cid_utbase import cid_UTBase
from futoin.cid.rmstool import RmsTool

import os, stat, fcntl
import subprocess
import glob
import shutil

class cid_config_Test ( cid_UTBase ) :
    __test__ = True
    TEST_DIR = os.path.join(cid_UTBase.TEST_RUN_DIR, 'config')
    _create_test_dir = True
    
    def setUp( self ):
        shutil.rmtree( self.TEST_DIR )
        os.mkdir(self.TEST_DIR)
        os.chdir(self.TEST_DIR)
        self._goToBase()

        os.mkdir('deploy_tmp')
        os.mkdir('current')
        os.mkdir('current/subdir')
        self._writeFile('.futoin-deploy.lock', '')

    def test_project_only(self):
        self._writeJSON('current/futoin.json', {
            'name': 'simple',
            'tools': {
                'hg': True,
            },
        })

        # in deploy
        self._call_cid(['tool', 'install'])
        res = self._call_cid(['tool', 'env'], retout=True)
        self.assertTrue('hgBin=' in res)
        self.assertFalse('svnBin=' in res)

        # in project
        os.chdir('current')
        res = self._call_cid(['tool', 'env'], retout=True)
        self.assertTrue('hgBin=' in res)
        self.assertFalse('svnBin=' in res)

        # in subdir
        os.chdir('subdir')
        res = self._call_cid(['tool', 'env'], retout=True)
        self.assertTrue('hgBin=' in res)
        self.assertFalse('svnBin=' in res)

    def test_deploy_only(self):
        self._writeJSON('futoin.json', {
            'name': 'simple',
            'tools': {
                'hg': True,
            },
        })

        # in deploy
        res = self._call_cid(['tool', 'env'], retout=True)
        self.assertTrue('hgBin=' in res)
        self.assertFalse('svnBin=' in res)

        # in project
        os.chdir('current')
        res = self._call_cid(['tool', 'env'], retout=True)
        self.assertTrue('hgBin=' in res)
        self.assertFalse('svnBin=' in res)

        # in subdir
        os.chdir('subdir')
        res = self._call_cid(['tool', 'env'], retout=True)
        self.assertTrue('hgBin=' in res)
        self.assertFalse('svnBin=' in res)

    def test_complex(self):
        self._writeJSON('futoin.json', {
            'name': 'simple',
            'tools': {
                'hg': True,
            },
        })
        self._writeJSON('current/futoin.json', {
            'name': 'simple',
            'tools': {
                'svn': True,
            },
        })

        # in deploy
        self._call_cid(['tool', 'install'])
        res = self._call_cid(['tool', 'env'], retout=True)
        self.assertTrue('hgBin=' in res)
        self.assertTrue('svnBin=' in res)

        # in project
        os.chdir('current')
        res = self._call_cid(['tool', 'env'], retout=True)
        self.assertTrue('hgBin=' in res)
        self.assertTrue('svnBin=' in res)

        # in subdir
        os.chdir('subdir')
        res = self._call_cid(['tool', 'env'], retout=True)
        self.assertTrue('hgBin=' in res)
        self.assertTrue('svnBin=' in res)

    def test_in_deploy(self):
        self._writeJSON('futoin.json', {
            'name': 'simple',
            'tools': {
                'hg': True,
            },
        })
        self._writeJSON('deploy_tmp/futoin.json', {
            'name': 'simple',
            'tools': {
                'svn': True,
            },
        })

        # in deploy
        res = self._call_cid(['tool', 'env'], retout=True)
        self.assertTrue('hgBin=' in res)
        self.assertFalse('svnBin=' in res)

        # in current
        os.chdir('current')
        res = self._call_cid(['tool', 'env'], retout=True)
        self.assertTrue('hgBin=' in res)
        self.assertFalse('svnBin=' in res)

        # in deploy tmp
        os.chdir('../deploy_tmp')
        res = self._call_cid(['tool', 'env'], retout=True)
        self.assertTrue('hgBin=' in res)
        self.assertTrue('svnBin=' in res)
