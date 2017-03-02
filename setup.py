try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
    
import sys

config = {
    'description': 'FutoIn Continuous Integration & Delivery Tool',
    'author': 'Andrey Galkin',
    'url': 'https://github.com/futoin/cid-tool',
    'download_url': 'https://github.com/futoin/cid-tool/archive/master.zip',
    'author_email': 'andrey@futoin.org',
    'version': '0.1',
    'install_requires': ['docopt'],
    'python_requires': '>=2.7',
    'packages': ['cid'],
    'scripts': [],
    'name': 'cid',
    'entry_points': {
        'console_scripts': [
            'cid=cid.cli:run',
            'cid%s=cid.cli:run' % sys.version[:1],
            'cid%s=cid.cli:run' % sys.version[:3],
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
