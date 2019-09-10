#!/bin/bash -e
/usr/bin/time  -f "run time: %U user %S system" timeout $UUT_TIMEOUT $1 $2 $3 $4
# if there is an error, this line is NOT executed ( "-e" )
# ...
