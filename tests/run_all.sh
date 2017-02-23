#!/bin/bash

if ! test -e bin/citool; then
    echo "Invoke from CITool project root!"
    exit 1
fi

tests=
tests+=" tests/citool_tools_test.py"
tests+=" tests/citool_git_test.py"
tests+=" tests/citool_hg_test.py"
tests+=" tests/citool_svn_test.py"

for nt in nosetests3 nosetests-3.4; do
    if which $nt; then
        echo "Python 3"
        $nt $tests;
        break
    fi
done

for nt in nosetests-2.7 nosetests; do
    if which $nt; then
        echo "Python 2"
        $nt $tests;
        break
    fi
done
