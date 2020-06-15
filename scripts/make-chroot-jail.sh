#!/bin/bash -ex
# https://gist.github.com/williamhaley/5a499cd7c83aa0e01eaf

#The current code does not work:
#
#bash-4.4# apt-get
#E: Unable to determine a suitable packaging system type



JAIL=/var/jail

mkdir -p $JAIL/{dev,etc,lib,lib64,usr,bin}
mkdir -p $JAIL/usr/bin
mkdir -p $JAIL/usr/sbin
# for apt-get
mkdir -p $JAIL/etc/apt/apt.conf.d
chown root.root $JAIL

mknod -m 666 $JAIL/dev/null c 1 3

JAIL_BIN=$JAIL/usr/bin/
JAIL_ETC=$JAIL/etc/

cp /etc/ld.so.cache $JAIL_ETC
cp /etc/ld.so.conf $JAIL_ETC
cp /etc/nsswitch.conf $JAIL_ETC
cp /etc/hosts $JAIL_ETC
cp -r /etc/apt/apt.conf.d $JAIL_ETC/apt/apt.conf.d

copy_binary()
{
	BINARY=$(which $1)

	cp $BINARY $JAIL/$BINARY

	copy_dependencies $BINARY
}

# http://www.cyberciti.biz/files/lighttpd/l2chroot.txt
copy_dependencies()
{
	FILES="$(ldd $1 | awk '{ print $3 }' |egrep -v ^'\(')"

	echo "Copying shared files/libs to $JAIL..."

	for i in $FILES
	do
		d="$(dirname $i)"

		[ ! -d $JAIL$d ] && mkdir -p $JAIL$d || :

		/bin/cp $i $JAIL$d
	done

	sldl="$(ldd $1 | grep 'ld-linux' | awk '{ print $1}')"

	# now get sub-dir
	sldlsubdir="$(dirname $sldl)"

	if [ ! -f $JAIL$sldl ];
	then
		echo "Copying $sldl $JAIL$sldlsubdir..."
		/bin/cp $sldl $JAIL$sldlsubdir
	else
		:
	fi
}

copy_binary ls
copy_binary sh
copy_binary bash
copy_binary git
copy_binary apt-get
copy_binary systemctl
copy_binary groupadd
copy_binary usermod
copy_binary newgrp
