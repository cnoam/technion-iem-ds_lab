#!/bin/bash -ex
# custom made for semester: 2020Spring, course:094219, ex:1
# $2 contains the full path to the data dir
data_path=$HOME/data/data
echo Running "$1" $data_path
echo Timeout set to $UUT_TIMEOUT

INPUT_SRC=`realpath $1`
GOLDEN=`realpath $3`
COMPARATOR=`realpath $4`

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
# part1
fname=part1/BirthStatistics.java
javac $fname
/usr/bin/time  -f "run time: %U user %S system"  timeout $UUT_TIMEOUT java $fname $data_path > output

# part2
fname=part2/Library.java
javac $fname part2/Book.java
timeout $UUT_TIMEOUT java $fname $2 >> output

#
echo --- finished the tested run.
set +e

echo Comparing output , $GOLDEN
python3 $COMPARATOR output $GOLDEN
retVal=$?
if [ $retVal -eq 42 ]; then
    echo "Sorry: actual output is different from the required output"
    exit 42
fi
if [ $retVal -ne 0 ]; then
    echo "Sorry: some error occured. Please examine the STDERR"
    exit 43
fi
popd
echo ---------- run OK
