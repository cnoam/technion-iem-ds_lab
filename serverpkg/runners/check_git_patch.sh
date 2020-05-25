#!/bin/bash -ex
# test changes to XV6 codebase:
#  apply git patch
# add my starting/ending code to terminate the xv6
#  make and run


echo Running $1 with args $2 $3 $4
echo Timeout set to $UUT_TIMOUT

INPUT_SRC=`realpath $1`
GOLDEN=`realpath $3`
COMPARATOR=`realpath $4`

TESTDIR=`mktemp -d`
MASTER_SRC_DIR=/data/xv6-public
PATCH_DIR=/data/patches
pushd $TESTDIR
cp -r $MASTER_SRC_DIR .

# copy with the .git so we can clearly see diffs
cd xv6-public
# start with a well known commit
git checkout 34f060c3dcf3bf3
git apply $INPUT_SRC --whitespace=nowarn
git apply  $PATCH_DIR/shutdown_syscall.patch --whitespace=nowarn
git apply  $PATCH_DIR/run_lsof_and_exit.patch --whitespace=nowarn

##### Both the patches should have been BEFORE the tested code -- do it next time...
# first compile etc. so random output does not contaminate the user's program output
make fs.img xv6.img  >& /dev/null
/usr/bin/time  -f "run time: %U user %S system" timeout $UUT_TIMEOUT make qemu-nox > output
# if there is an error, this line is NOT executed ( "-e" )
# ...


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
