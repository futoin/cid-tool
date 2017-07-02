
class CurlToolMixIn(object):
    __slots__ = ()

    def getDeps(self):
        return ['curl']

    def _callCurl(self, env, curl_args, *args, **nargs):
        timeout_args = self._configutil.timeouts(env, 'curl')

        return self._executil.callExternal(
            [env['curlBin'], '-fsSL'] + timeout_args + curl_args,
            *args, **nargs
        )
