#!/bin/bash -ex

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

# must have ENV_VAR $UUT_TIMEOUT defined and have int value (seconds)

function Usage()
{
    echo "Usage:"
    echo "check_python some_file.tar.gz input_data_file the_needed_output full/path/to/compare/script"
}

if [ -z "$4" ]; then
 Usage
 exit 40
fi

# extract a file from [py,zip,gz,xz] to current dir
function extract()
{
  echo extracting $1
  if [[ $1 == *.py ]]; then
    echo "already a python file"
    cp $1 main.py # use cp to keep same behavior as other files - the original is untouched(?).
  elif [[ $1 == *.zip ]]; then
     unzip $1
  elif [[ ( $1 == *.xz ) || ( $1 == *.tar.gz ) ]]; then
     tar xf $1
  elif [[ ( $1 == *.gz ) ]]; then
     mv $1 ./main.py.gz
     gunzip ./main.py.gz
  fi
}

INPUT_TAR=`realpath $1`
INPUT_DATA=`realpath $2`
GOLDEN=`realpath $3`
COMPARATOR=`realpath $4`

TESTDIR=`mktemp -d`
pushd /tmp
rm -rf $TESTDIR
mkdir $TESTDIR
cd $TESTDIR
extract $INPUT_TAR

# do not remove the tempdir, to allow for postmortem

EXE=main.py
echo --- about to run: python $EXE $INPUT_DATA
/usr/bin/time  -f "run time: %U user %S system"  timeout $UUT_TIMEOUT python $EXE $INPUT_DATA > output
echo --- finished the tested run.
set +e

echo Comparing output , $GOLDEN
python3 $COMPARATOR output $GOLDEN
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


