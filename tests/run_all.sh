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

echo "Python 3"
nosetests3 $tests

echo "Python 2"
nosetests $tests
