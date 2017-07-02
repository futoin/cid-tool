
class JavaToolMixIn(object):
    __slots__ = ()

    _LATEST_JAVA = '8'

    def _minJava(self):
        return None

    def envDeps(self, env):
        min_java = self._minJava()

        if not min_java:
            return

        for ek in ['javaVer', 'jdkVer']:
            if env.get(ek, None):
                if int(env[ek]) < int(min_java):
                    self._errorExit('{0} requires minimal {1}={2}'
                                    .format(self._name, ek, min_java))
            else:
                env[ek] = str(self._LATEST_JAVA)
