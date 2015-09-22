try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'FutoIn CI Tool',
    'author': 'Andrey Galkin',
    'url': 'https://github.com/futoin/citool',
    'download_url': 'https://github.com/futoin/citool/archive/master.zip',
    'author_email': 'andrey@futoin.org',
    'version': '0.1',
    'install_requires': ['nose','docopt'],
    'packages': ['citool'],
    'scripts': [],
    'name': 'citool'
}

setup(**config)
