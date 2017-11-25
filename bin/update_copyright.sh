#!/bin/bash

mpath=$(dirname $0)/..

if test -z "$mpath"; then
    echo "Usage: $(basename $0) module path)"
fi

author="Andrey Galkin <andrey@futoin.org>"
year=$(date +"%Y")

function update_license_file() {
    update_py_file $1
}

function update_py_file() {
    local f=$1
    local ftmp=${f}.tmp
    
    if egrep -q "Copyright [0-9]{4}(-[0-9]{4})? $author" $f; then
        awk "
        /Copyright $year $author/ { print; next }
        /Copyright ([0-9]{4})-$year $author/ { print; next }
        /Copyright ([0-9]{4})(-[0-9]{4})? $author/ {
            print gensub(/([0-9]{4})(-[0-9]{4})?/, \"\\\\1-$year\", \"g\")
            next
        }
        {print}
        " $f > $ftmp

        if diff -q $f $ftmp; then
            rm -f $ftmp
        else
            mv -f $ftmp $f
        fi
        return
    fi
    
    cat >$ftmp <<EOT
#
# Copyright $year $author
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

EOT

    cat $f >>$ftmp
    mv $ftmp $f
}

#update_license_file $mpath/LICENSE

for f in $(find $mpath -type f -name '*.py' | grep -v '/contrib/'); do
    update_py_file $f
done


