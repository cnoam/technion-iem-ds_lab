#!/bin/bash -e
echo Running $1 with args $2 $3 $4
echo Timeout set to $UUT_TIMOUT
/usr/bin/time  -f "run time: %U user %S system" timeout $UUT_TIMEOUT $1 $2 $3 $4
# if there is an error, this line is NOT executed ( "-e" )
# ...
