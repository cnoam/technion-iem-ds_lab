#!/bin/bash -e

#This script takes as input a tar.gz file that contains source code and CMake file.
#
#1. extract the files
#2. run cmake
#3. run make
#4. run the executable
#5. compare the output (stdout) to the supplied golden reference and return pass/fail
#
# return value:
# 0     full success
# any other value - failure of some sort

function Usage()
{
    echo "Usage:"
    echo "checker  some_file.tar.gz input_data_file the_needed_output"
}

if [ -z "$3" ]; then
 Usage
 exit 1
fi

INPUT_TAR=`realpath $1`
INPUT_DATA=`realpath $2`
GOLDEN=`realpath $3`
TESTDIR=`mkdir -d`
pushd ./tmp
rm -rf $TESTDIR
mkdir $TESTDIR
cd $TESTDIR
tar xf $INPUT_TAR
cmake .
make
echo ----------- compilation OK
# do not remove the tempdir, to allow for postmortem

# run the exe. what's its name?
EXE=`find .  -maxdepth 1 -type f   -executable`
num_exe=`echo $EXE | wc -w`
if [ $num_exe -ne 1 ]; then
    echo ERROR: There should be exactly one executable file in this dir
    echo You have these files:    $EXE
    exit 2
fi
./$EXE $INPUT_DATA > output
set +e
cmp output $GOLDEN
if [ $? -ne 0 ]; then
    echo "Sorry: output is different from the required output (or some other error)"
    exit 3
fi
popd
echo ---------- run OK


