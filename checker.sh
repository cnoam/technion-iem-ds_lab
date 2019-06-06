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

echo "before"
sleep 2
echo "after"
>&2 echo "to stderrrrr"
exit 1

function Usage()
{
    echo "Usage:"
    echo "checker  some_file.tar.gz input_data_file the_needed_output"
}

# write to stdout the content of f after trimming some of the white spaces
function canon()
{
	sed -r 's/\ //gm' $1
}

# compare two files , ignoring spaces that appear after ^.*:  
function compare_ignore_spaces()
{
	a=$1
	b=$2
	A=`mktemp `
	B=`mktemp `
	canon $a > $A
	canon $b > $B
	diff $A $B
	R=$?
	return  $R
}

if [ -z "$3" ]; then
 Usage
 exit 1
fi

INPUT_TAR=`realpath $1`
INPUT_DATA=`realpath $2`
GOLDEN=`realpath $3`
TESTDIR=`mktemp -d`
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
echo --- about to run: $EXE $INPUT_DATA
$EXE $INPUT_DATA > output
echo --- finished the tested run.
set +e
# The direct compare is good for hw1 and 2 but not for 3
# compare_ignore_spaces output $GOLDEN

# for ex3:
python tester_ex3.py output $GOLDEN
if [ $? -ne 0 ]; then
    echo "Sorry: output is different from the required output (or some other error)"
    exit 3
fi
popd
echo ---------- run OK


