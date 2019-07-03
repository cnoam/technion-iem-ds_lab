#!/bin/bash -e
# run the code in $1, without network, with timeout
/usr/bin/time  -f "run time: %U user %S system" timeout $UUT_TIMEOUT unshare -r -n $1 $2 $3 $4
# if there is an error, this line is NOT executed ( "-e" )
# ...
