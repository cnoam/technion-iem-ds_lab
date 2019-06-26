#!/bin/bash -e

#This script takes as input a tar.{gz,xz} file that contains source code in python.
#
#1. extract the files
#2. run main.py
#3. compare the output (stdout) to the supplied golden reference and return pass/fail
#
# return value:
# 0     full success
# any other value - failure of some sort
echo running $0 $1 $2 $3 $4

function Usage()
{
    echo "Usage:"
    echo "check_python some_file.tar.gz input_data_file the_needed_output full/path/to/compare/script"
}

if [ -z "$4" ]; then
 Usage
 exit 40
fi

INPUT_TAR=`realpath $1`
INPUT_DATA=`realpath $2`
GOLDEN=`realpath $3`
COMPARATOR=`realpath $4`

TESTDIR=`mktemp -d`
pushd ./tmp
rm -rf $TESTDIR
mkdir $TESTDIR
cd $TESTDIR
tar xf $INPUT_TAR

# do not remove the tempdir, to allow for postmortem

# run the exe. what's its name?
EXE=main.py
echo --- about to run: python $EXE $INPUT_DATA
/usr/bin/time  -f "run time: %U user %S system"  python $EXE $INPUT_DATA > output
echo --- finished the tested run.
set +e

echo Comparing output , $GOLDEN
python $COMPARATOR output $GOLDEN
retVal=$?
if [ $retVal -eq 42 ]; then
    echo "Sorry: output is different from the required output"
    exit 42
fi
if [ $retVal -ne 0 ]; then
    echo "Sorry: some error occured. Please examine the STDERR"
    exit 43
fi
popd
echo ---------- run OK


