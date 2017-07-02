
import importlib as _importlib
import sys
import os

__all__ = [
    'tailor_ondemand',
    'ext_demander',
    'OnDemandMixIn',
]

#---


def tailor_ondemand(demandMap):
    class TailoredDemander(object):
        __slots__ = tuple(demandMap.keys())
        __demandMap = demandMap

        def __getattr__(self, name):
            mod = TailoredDemander.__demandMap[name]

            if isinstance(mod, tuple):
                mod, memb = mod
                mod = _importlib.import_module(mod, 'futoin.cid')
                ret = getattr(mod, memb)
            else:
                ret = _importlib.import_module(mod, 'futoin.cid')

            setattr(self, name, ret)
            return ret

    return TailoredDemander


#---
_ext_demand_map = {
    'shlex': 'shlex',
    'subprocess': 'subprocess',
    'json': 'json',
    'datetime': 'datetime',
    're': 're',
    'gzip': 'gzip',
    'shutil': 'shutil',
    'stat': 'stat',
    'time': 'time',
    'fnmatch': 'fnmatch',
    'fcntl': 'fcntl',
    'hashlib': 'hashlib',
    'signal': 'signal',
    'copy': 'copy',
    'errno': 'errno',
    'pwd': 'pwd',
    'grp': 'grp',
    'glob': 'glob',
    'dir_util': 'distutils.dir_util',
    'requests': 'requests',
    'minidom': 'xml.dom.minidom',
    'importlib': 'importlib',
    'tempfile': 'tempfile',
    'resource': 'resource',
    'binascii': 'binascii',
}

if sys.version_info >= (3, 0):
    _ext_demand_map['urllib'] = 'urllib.request'
else:
    _ext_demand_map['urllib'] = 'urllib2'

ext_demander = tailor_ondemand(_ext_demand_map)()

#---
_cid_demand_map = {
    '_os': 'os',
    '_ospath': 'os.path',
    '_sys': 'sys',
    '_detect': '.util.detect',
    '_exec': '.util.exec',
    '_package': '.util.package',
    '_path': '.util.path',
}


class OnDemandMixIn(tailor_ondemand(_cid_demand_map)):
    __slots__ = ()
    _ext = ext_demander
    _environ = os.environ
