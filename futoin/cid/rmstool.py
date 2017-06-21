
from __future__ import print_function, absolute_import

from .subtool import SubTool
from .coloring import Coloring

__all__ = ['RmsTool']


class RmsTool(SubTool):
    ALLOWED_HASH_TYPES = [
        'md5',
        'sha1',
        'sha256',
        'sha512',
    ]

    def autoDetect(self, config):
        if self._autoDetectRMS(config):
            return True

        return super(RmsTool, self).autoDetect(config)

    def rmsUpload(self, config, rms_pool, package_list):
        raise NotImplementedError(self._name)

    def rmsPromote(self, config, src_pool, dst_pool, package_list):
        raise NotImplementedError(self._name)

    def rmsGetList(self, config, rms_pool, package_hint):
        raise NotImplementedError(self._name)

    def rmsRetrieve(self, config, rms_pool, package_list):
        raise NotImplementedError(self._name)

    def rmsPoolCreate(self, config, rms_pool):
        raise NotImplementedError(self._name)

    def rmsPoolList(self, config):
        raise NotImplementedError(self._name)

    def rmsGetHash(self, config, rms_pool, package, hash_type):
        raise NotImplementedError(self._name)

    def _autoDetectRMS(self, config):
        if config.get('rms', None) == self._name:
            return True

        return False

    def rmsProcessChecksums(self, config, rms_pool, package_list):
        ret = []

        for package in package_list:
            package = package.split('@', 1)
            filename = package[0]

            if len(package) == 2:
                hash_str = package[1]
                hash_type, hash = hash_str.split(':', 1)

                if hash_type not in self.ALLOWED_HASH_TYPES:
                    self._errorExit(
                        'Unsupported hash type "{0}"'.format(hash_type))

                self._info('Verifying {2} hash of {0} in {1}'.format(
                    filename, rms_pool, hash_type))
                rms_hash = self.rmsGetHash(
                    config, rms_pool, filename, hash_type)

                if rms_hash != hash:
                    self._errorExit(
                        'RMS hash mismatch "{0}" != "{1}"'.format(rms_hash, hash))

            ret.append(filename)

        return ret

    @classmethod
    def rmsCalcHash(cls, file_name, hash_type):
        import hashlib

        hf = hashlib.new(hash_type)
        with open(file_name, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), ''):
                if not chunk:
                    break
                hf.update(chunk)
        return "{0}:{1}".format(hash_type, hf.hexdigest())

    @classmethod
    def rmsCalcHashes(cls, file_name):
        import hashlib

        hashes = {}

        for hash_type in cls.ALLOWED_HASH_TYPES:
            hashes[hash_type] = hashlib.new(hash_type)

        with open(file_name, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), ''):
                if not chunk:
                    break

                for hash_type in cls.ALLOWED_HASH_TYPES:
                    hashes[hash_type].update(chunk)

        for hash_type in cls.ALLOWED_HASH_TYPES:
            hashes[hash_type] = hashes[hash_type].hexdigest()

        return hashes
