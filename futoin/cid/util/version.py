
from ..mixins.ondemand import ext as _ext


def sort(verioned_list):
    def castver(v):
        res = _ext.re.split(r'[\W_]+', v)
        for (i, vc) in enumerate(res):
            try:
                res[i] = int(vc, 10)
            except:
                pass
        return res

    verioned_list.sort(key=castver)


def latest(verioned_list):
    sort(verioned_list)
    return verioned_list[-1]
