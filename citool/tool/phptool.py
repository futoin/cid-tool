
from citool.subtool import SubTool
import os, fnmatch

class phpTool( SubTool ):
    PHP_DIR = os.path.join(os.environ['HOME'], '.php')
    PHP_SYSTEM_VER = 'system'

    def getType( self ):
        return self.TYPE_RUNTIME
    
    def getDeps( self ) :
        return [ 'bash', 'phpbuild' ]
    
    def _installTool( self, env ):
        php_ver = env['phpVer']
        
        if php_ver == self.PHP_SYSTEM_VER:
            self._systemDeps()
            return SubTool._installTool(self, env)
        
        self._buildDeps()

        php_dir = env['phpDir']
        
        try: os.makedirs(php_dir)
        except: pass

        old_tmpdir = os.environ.get('TMPDIR', '/tmp')
        os.environ['TMPDIR'] = os.path.join(php_dir, '..')
        self._callExternal( [ env['phpbuildBin'], php_ver, env['phpDir'] ] )
        os.environ['TMPDIR'] = old_tmpdir
    
    def updateTool( self, env ):
        pass
    
    def uninstallTool( self, env ):
        if env['phpVer'] == self.PHP_SYSTEM_VER:
            return SubTool.uninstallTool(self, env)

        self._callExternal(
            [ env['bashBin'],  '--noprofile', '--norc', '-c',
              'chmod -R g+w {0}; rm -rf {0}'
               .format(env['phpDir']) ] )
        self._have_tool = False
    
    def _envNames( self ) :
        return ['phpDir', 'phpBin', 'phpVer']
    
    def initEnv( self, env ) :
        php_ver = env.setdefault('phpVer', self.PHP_SYSTEM_VER)
        
        if php_ver == self.PHP_SYSTEM_VER:
            env.setdefault('phpDir', '/usr')
            return SubTool.initEnv(self, env)
        else:
            def_dir = os.path.join(env['phpbuildDir'], 'share', 'php-build', 'definitions')
            defs = os.listdir(def_dir)
            defs = fnmatch.filter(defs, php_ver + '*')
            
            if not defs:
                raise RuntimeError('PHP version %s not found' % php_ver)
            
            def castver(v):
                try: return int(v)
                except: return -1
            
            defs.sort(key=lambda v: [castver(u) for u in v.split('.')])
            php_ver = defs[-1]
            
            env['phpVer'] = php_ver
        
        php_dir = env.setdefault('phpDir', os.path.join(self.PHP_DIR, php_ver))
        php_bin_dir = os.path.join(php_dir, 'bin')
        php_bin = os.path.join(php_bin_dir, 'php')
        
        if os.path.exists(php_bin):
            self._have_tool = True
            self.addBinPath( php_bin_dir )
            env.setdefault('phpBin', php_bin)
            
    def _buildDeps( self ):
        os.environ['PHP_BUILD_CONFIGURE_OPTS'] = ' \
            --with-libdir=lib/x86_64-linux-gnu \
            --disable-debug \
            --with-regex=php \
            --enable-calendar \
            --enable-sysvsem \
            --enable-sysvshm \
            --enable-sysvmsg \
            --enable-bcmath \
            --disable-cgi \
            --enable-fpm \
            --with-fpm-systemd \
            --with-bz2 \
            --enable-ctype \
            --without-db4 \
            --without-qdbm \
            --without-gdbm \
            --with-iconv \
            --enable-exif \
            --enable-ftp \
            --with-gettext \
            --enable-mbstring \
            --with-onig=/usr \
            --with-pcre-regex=/usr \
            --enable-shmop \
            --enable-sockets \
            --enable-wddx \
            --with-libxml-dir=/usr \
            --with-zlib \
            --with-kerberos=/usr \
            --with-openssl=/usr \
            --enable-soap \
            --enable-zip \
            --with-mhash=yes \
            --with-system-tzdata \
            '
            #--with-db4 \
            #--with-qdbm=/usr \
        
        self.require_deb([
            'build-essential',
            'libsystemd-dev',
            'libcurl4-openssl-dev',
            'libtidy-dev',
            'libpng-dev',
            'libmcrypt-dev',
            'libjpeg-dev',
            'libreadline-dev',
            'libbz2-dev',
            'libc-client-dev',
            'libdb-dev',
            'libedit-dev',
            'libenchant-dev',
            'libevent-dev',
            'libexpat1-dev',
            'libfreetype6-dev',
            'libgcrypt11-dev',
            'libgd2-dev',
            'libglib2.0-dev',
            'libgmp3-dev',
            'libicu-dev',
            'libjpeg-dev',
            'libkrb5-dev',
            'libldap2-dev',
            'libmagic-dev',
            'libmhash-dev',
            'libmysqlclient-dev',
            'libonig-dev',
            'libpam0g-dev',
            'libpcre3-dev',
            'libpng-dev',
            'libpq-dev',
            'libpspell-dev',
            'libqdbm-dev',
            'librecode-dev',
            'libsasl2-dev',
            'libsnmp-dev',
            'libsqlite3-dev',
            'libssl-dev',
            'libwrap0-dev',
            'libxmltok1-dev',
            'libxml2-dev',
            'libvpx-dev',
            'libxslt1-dev',
            'unixodbc-dev',
            'zlib1g-dev',
            're2c',
        ])
    
    def _systemDeps( self ):
        self.require_deb([
            'php.*-cli',
            'php.*-fpm',
            "php.*-apcu",
            "php.*-curl",
            "php.*-gd",
            "php.*-geoip",
            "php.*-gmp",
            "php.*-imagick",
            "php.*-imap",
            "php.*-intl",
            "php.*-json",
            "php.*-ldap",
            "php.*-mbstring",
            "php.*-mcrypt",
            "php.*-msgpack",
            "php.*-opcache",
            "php.*-ssh2",
            "php.*-soap",
            "php.*-xml",
            "php.*-xmlrpc",
            "php.*-xsl",
            "php.*-zip",
        ])

        