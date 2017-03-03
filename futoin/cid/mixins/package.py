
from __future__ import print_function, absolute_import

class PackageMixIn( object ):
    @classmethod
    def requireDeb(cls, packages):
        apt_get = cls._which('apt-get')
        
        if apt_get:
            try: cls._callExternal(['sudo', '--non-interactive', apt_get, 'install', '-y'] + packages)
            except: print('WARNING: you may need to install build deps manually !')

    @classmethod
    def requireYum(cls, packages):
        yum = cls._which('yum')
        
        if yum:
            try: cls._callExternal(['sudo', '-n', yum, 'install', '-y'] + packages)
            except: print('WARNING: you may need to install build deps manually !')

    @classmethod
    def requireZypper(cls, packages):        
        zypper = cls._which('zypper')

        if zypper:
            try: cls._callExternal(['sudo', '-n', zypper, 'install', '-y'] + packages)
            except: print('WARNING: you may need to install build deps manually !')
            
    @classmethod
    def requireRpm(cls, packages):
        cls.requireYum(packages)
        cls.requireZypper(packages)
    
    @classmethod
    def requirePackages(cls, packages):
        cls.requireDeb(packages)
        cls.requireRpm(packages)
