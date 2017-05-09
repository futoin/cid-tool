
class CurlToolMixIn(object):
    def getDeps(self):
        return ['curl']

    def _callCurl(self, env, curl_args, *args, **nargs):
        timeout_args = self._timeouts(env, 'curl')

        return self._callExternal(
            [env['curlBin'], '-fsSL'] + timeout_args + curl_args,
            *args, **nargs
        )
