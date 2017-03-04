
from setuptools import setup, find_packages
    
import os, sys

sys.path.insert( 0, os.path.dirname( __file__ ) )
from futoin.cid import __version__ as version

config = {
    'description': 'FutoIn Continuous Integration & Delivery Tool',
    'author': 'Andrey Galkin',
    'url': 'https://github.com/futoin/cid-tool',
    'download_url': 'https://github.com/futoin/cid-tool/archive/master.zip',
    'author_email': 'andrey@futoin.org',
    'version': version,
    'install_requires': ['docopt'],
     'extras_require': {
        'test': ['nose'],
    },
    'python_requires': '>=2.7',
    'packages': find_packages(exclude=['bind', 'tests']),
    'name': 'futoin-cid',
    'entry_points': {
        'console_scripts': [
            'cid=futoin.cid.cli:run',
            'cid%s=futoin.cid.cli:run' % sys.version[:1],
            'cid%s=futoin.cid.cli:run' % sys.version[:3],
            'futoin-cid=futoin.cid.cli:run',
            'futoin-cid%s=futoin.cid.cli:run' % sys.version[:1],
            'futoin-cid%s=futoin.cid.cli:run' % sys.version[:3],
        ],
    },
    'classifiers': [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Software Development :: Build Tools',
        'Topic :: System :: Installation/Setup',
        'Programming Language :: JavaScript',
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
        'Environment :: Console',
    ],
    'keywords': 'php ruby node nodejs npm gem rvm nvm grunt gulp bower puppet build deploy futoin',
    'license': 'Apache 2.0',
}

setup(**config)
