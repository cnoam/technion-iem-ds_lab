#!/bin/bash -e

#This script takes as input a tar.{gz,xz} file that contains source code in python.
#
#1. extract the files
#2. copy tester_ex9.py to the same dir
#3. run tester_ex9
#4. write the score (if success) to the DB
# return value:
# 0     full success
# any other value - failure of some sort
echo running $0 $1 $2

TEST_RUNNER='tester_ex9.py'
# must have ENV_VAR $UUT_TIMEOUT defined and have int value (seconds)

function Usage()
{
    echo "Usage:"
    echo "check_python some_file.tar.gz input_data_file  full/path/to/compare/script"
}

if [ -z "$2" ]; then
 Usage
 exit 40
fi

# extract a file from [py,zip,gz,xz] to current dir
function extract()
{
  if [[ $1 == *.py ]]; then
    echo "already a python file"
  fi
  if [[ $1 == *.zip ]]; then
     gzunip $1
  fi
  if [[ ( $1 == *.xz ) || ( $1 == *.gz ) ]]; then
     tar xf $1
  fi

}

INPUT_TAR=`realpath $1`
INPUT_DATA=`realpath $2`
if [ -z "$UUT_TIMEOUT" ];then
    echo "Setting default timeout to 60 seconds"
    UUT_TIMEOUT=60
fi

TESTDIR=`mktemp -d`
rm -rf $TESTDIR
mkdir $TESTDIR
cp server_codes.py $TESTDIR
cp $TEST_RUNNER $TESTDIR/
cp $INPUT_TAR $TESTDIR/
cd $TESTDIR
extract $INPUT_TAR

# do not remove the tempdir, to allow for postmortem
/usr/bin/time  -f "run time: %U user %S system"  timeout $UUT_TIMEOUT python3 $TEST_RUNNER $INPUT_DATA
retVal=$?
echo --- finished the tested run.
set +e

if [ $retVal -ne 0 ]; then
    echo "Sorry: some error occured. Please examine the STDERR"
    exit 43
fi
echo ---------- run OK


