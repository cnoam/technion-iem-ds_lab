#!/bin/bash -e

#This script takes as input a tar.{gz,xz} file that contains source code and CMake file.
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
echo running $0 $1 $2 $3 $4

function Usage()
{
    echo "Usage:"
    echo "checker_cmake  some_file.tar.gz input_data_file the_needed_output full/path/to/compare/script"
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

if [ -z "$4" ]; then
 Usage
 exit 40
fi

INPUT_TAR=`realpath $1`
INPUT_DATA=`realpath $2`
GOLDEN=`realpath $3`
COMPARATOR=`realpath $4`

TESTDIR=`mktemp -d`
pushd /tmp
rm -rf $TESTDIR
mkdir $TESTDIR
cd $TESTDIR
tar xf $INPUT_TAR

# make sure the source files are not marked as executable
chmod a-x ./*
# make sure users did not upload this cache by mistake - it confuses the cmake
rm -rf CMakeCache.txt
cmake .
# -DCMAKE_BUILD_TYPE=Release .
make
echo ----------- compilation OK
# do not remove the tempdir, to allow for postmortem

# run the exe. what's its name?
EXE=`find .  -maxdepth 1 -type f   -executable`
num_exe=`echo $EXE | wc -w`
if [ $num_exe -ne 1 ]; then
    echo ERROR: There should be exactly one executable file in this dir
    echo You have these files:    $EXE
    exit 41
fi
echo --- about to run: $EXE $INPUT_DATA
/usr/bin/time  -f "run time: %U user %S system" timeout $UUT_TIMEOUT $EXE $INPUT_DATA > output
echo --- finished the tested run.
set +e

echo Comparing output , $GOLDEN
python $COMPARATOR output $GOLDEN
retVal=$?

# ExitCode.COMPARE_FAILED == 42
if [ $retVal -eq 42 ]; then
    echo "Sorry: output is different from the required output"
fi
if [ $retVal -ne 0 ]; then
    echo "Sorry: some error occured. Please examine the STDERR"
fi
popd
exit $retVal
echo ---------- run OK


