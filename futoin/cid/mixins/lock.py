
from .data import DataSlots


class LockMixIn(DataSlots):
    __slots__ = ()

    __DEPLOY_LOCK_FILE = '.futoin-deploy.lock'
    __MASTER_LOCK_FILE = '.futoin-master.lock'
    __GLOBAL_LOCK_FILE = '.futoin-global.lock'

    def __init__(self):
        super(LockMixIn, self).__init__()
        self._deploy_lock = None
        self._master_lock = None
        self._global_lock = None

    def __lockCommon(self, lock, file, flags):
        fcntl = self._ext.fcntl
        os = self._os

        assert getattr(self, lock) is None

        lockfd = os.open(file, os.O_WRONLY | os.O_CREAT)
        setattr(self, lock, lockfd)

        try:
            fcntl.flock(lockfd, flags)
        except Exception as e:
            self._errorExit('FAILED to acquire{0}: {1}'.format(
                lock.replace('_', ' '), e))

    def __unlockCommon(self, lock):
        fcntl = self._ext.fcntl
        lockfd = getattr(self, lock)
        fcntl.flock(lockfd, fcntl.LOCK_UN)
        self._os.close(lockfd)
        setattr(self, lock, None)

    def _deployLock(self):
        fcntl = self._ext.fcntl
        self.__lockCommon(
            '_deploy_lock',
            self.__deployLockFile(),
            fcntl.LOCK_EX | fcntl.LOCK_NB
        )

    def _deployUnlock(self):
        self.__unlockCommon('_deploy_lock')

    def _requireDeployLock(self):
        if self._deploy_lock is None:
            self._errorExit('Deploy lock must be already acquired')

    def _globalLock(self):
        fcntl = self._ext.fcntl
        self.__lockCommon(
            '_global_lock',
            self.__globalLockFile(),
            fcntl.LOCK_EX
        )

    def _globalUnlock(self):
        self.__unlockCommon('_global_lock')

    def _masterLock(self):
        fcntl = self._ext.fcntl
        self.__lockCommon(
            '_master_lock',
            self.__masterLockFile(),
            fcntl.LOCK_EX | fcntl.LOCK_NB
        )

    def _masterUnlock(self):
        self.__unlockCommon('_master_lock')

    def __deployLockFile(self):
        return self._ospath.join(self._overrides['deployDir'], self.__DEPLOY_LOCK_FILE)

    def __masterLockFile(self):
        return self._ospath.join(self._overrides['deployDir'], self.__MASTER_LOCK_FILE)

    def __globalLockFile(self):
        return self._ospath.join(self._environ['HOME'], self.__GLOBAL_LOCK_FILE)

    def _checkDeployLock(self):
        ospath = self._ospath
        placeholder = self.__deployLockFile()
        deploy_dir = self._overrides['deployDir']

        if not ospath.exists(placeholder) and self._os.listdir(deploy_dir):
            self._errorExit(
                "Deployment dir '{0}' is missing safety placeholder {1}."
                .format(deploy_dir, ospath.basename(placeholder))
            )
