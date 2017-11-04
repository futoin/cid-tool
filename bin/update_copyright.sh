#!/bin/bash

mpath=$(dirname $0)/..

if test -z "$mpath"; then
    echo "Usage: $(basename $0) module path)"
fi

author="Andrey Galkin"
year=$(date +"%Y")

function update_license_file() {
    update_py_file $1
}

function update_py_file() {
    local f=$1
    local ftmp=${f}.tmp
    
    if egrep -q "Copyright [0-9]{4}(-[0-9]{4})? \(c\) $author" $f; then
        awk "
        /Copyright $year \(c\) $author/ { print; next }
        /Copyright ([0-9]{4})-$year \(c\) $author/ { print; next }
        /Copyright ([0-9]{4})(-[0-9]{4})? \(c\) $author/ {
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
# Copyright $year (c) $author
#

EOT

    cat $f >>$ftmp
    mv $ftmp $f
}

update_license_file $mpath/LICENSE

for f in $(find $mpath -type f -name '*.py' | grep -v '/contrib/'); do
    update_py_file $f
done


