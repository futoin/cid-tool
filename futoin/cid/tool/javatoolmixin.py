
class JavaToolMixIn(object):
    _LATEST_JAVA = '8'
    _MIN_JAVA = None

    def envDeps(self, env):
        if not self._MIN_JAVA:
            return

        for ek in ['javaVer', 'jdkVer']:
            if env.get(ek, None):
                if int(env[ek]) < int(self._MIN_JAVA):
                    self._errorExit('{0} requires minimal {1}={2}'
                                    .format(self._name, ek, self._MIN_JAVA))
            else:
                env[ek] = str(self._LATEST_JAVA)
