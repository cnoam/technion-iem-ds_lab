#!/bin/bash
set -exuo pipefail
# custom made for semester: 2020Spring, course:094219, ex:3
# $2 contains the full path to the data dir
echo Running "$1" "$2" "$3" "$4 $5"
echo Timeout set to "$UUT_TIMEOUT"

INPUT_SRC=`realpath $1`
INPUT_DATA=`realpath $2`
GOLDEN=`realpath $3`
COMPARATOR=`realpath $4`
DATA_DIR=`realpath $5`

TESTDIR=`mktemp -d`
pushd /tmp
rm -rf $TESTDIR
mkdir $TESTDIR
cd $TESTDIR
echo PWD="`pwd`"

#unshare -rn /usr/bin/time  -f "run time: %U user %S system" timeout $UUT_TIMEOUT java $1 $2 $3 $4
# if there is an error, this line is NOT executed ( "-e" )
# ...

# extract the zip, cd to src, compile and run
unzip $INPUT_SRC
cd src

fname=DocumentRetrieval
javac $fname.java

echo ==== compilation OK ====
# write the output to both stdout and local file.
# the local file is used for pass/fail checking here (but in the future might be moved to inside the python code)
/usr/bin/time  -f "run time: %U user %S system"  timeout $UUT_TIMEOUT java $fname  $DATA_DIR $INPUT_DATA | tee output

echo ==== finished the tested run ====
set +e

echo Comparing output , $GOLDEN
python3 $COMPARATOR output $GOLDEN
retVal=$?
if [ $retVal -eq 42 ]; then
    echo "Sorry: actual output is different from the required output"
    exit 42
fi
if [ $retVal -ne 0 ]; then
    echo "Sorry: some error occurred. Please examine the STDERR"
    exit 43
fi
popd
echo ---------- run OK
