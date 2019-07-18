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

from setuptools import setup, find_packages
    
import os, sys

project_path = os.path.dirname( __file__ )
sys.path.insert( 0, project_path )
from futoin.cid import __version__ as version

with open(os.path.join(project_path, 'README.rst'), 'r') as f:
    long_description = f.read()

config = {
    'name': 'futoin-cid',
    'version': version,
    'namespace_packages': ['futoin'],

    'description': 'FutoIn Continuous Integration & Delivery Tool',
    'long_description': long_description,

    'author': 'Andrey Galkin',
    'author_email': 'andrey@futoin.org',

    'url': 'https://github.com/futoin/cid-tool',
    'download_url': 'https://github.com/futoin/cid-tool/archive/master.zip',

    'install_requires': [
        'docopt',
        #'requests>=2.18.4',
        # be compatible with docker/docker-compose
        'requests>=2.5.2',
        'urllib3>=1.21.1',
    ],
    # temporary disabled due to py3 failures on setup of pylint
    #'setup_requires': ['autopep8', 'pylint'],
    'extras_require': {
        'test': ['nose'],
    },
    'python_requires': '>=2.7',
    'packages': find_packages(exclude=['bind', 'tests']),
    
    'entry_points': {
        'console_scripts': [
            'cid=futoin.cid.cli:run',
            'cte=futoin.cid.cte:run',
            'futoin-cid=futoin.cid.cli:run',
        ],
    },
    'classifiers': [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: C',
        'Programming Language :: C++',
        'Programming Language :: Java',
        'Programming Language :: JavaScript',
        'Programming Language :: Other',
        'Programming Language :: PHP',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Ruby',
        'Programming Language :: Unix Shell',
        'Topic :: Software Development :: Build Tools',
        'Topic :: System :: Installation/Setup',
        'Topic :: Utilities',
    ],
    'keywords': 'php ruby node nodejs npm gem rvm nvm grunt gulp bower \
 puppet build deploy futoin cmake make gradle maven java composer bundler',
    'license': 'Apache 2.0',
}

setup(**config)
