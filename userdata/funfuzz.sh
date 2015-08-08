#! /bin/bash -ex
# https://help.ubuntu.com/community/CloudInit
# http://www.knowceantech.com/2014/03/amazon-cloud-bootstrap-with-userdata-cloudinit-github-puppet/
export DEBIAN_FRONTEND=noninteractive  # Bypass ncurses configuration screens

# -----------------------------------------------------------------------------

# Backup ubuntu user folder files as we will then mount the instance store to it
mkdir /ubuntuUser-old/
cp -pRP /home/ubuntu/.bash_logout /ubuntuUser-old/
cp -pRP /home/ubuntu/.bashrc /ubuntuUser-old/
cp -pRP /home/ubuntu/.profile /ubuntuUser-old/
cp -pRP /home/ubuntu/.ssh/authorized_keys /ubuntuUser-old/
rm -rf /home/ubuntu/

# Format and mount all available instance stores.
# Adapted from http://stackoverflow.com/a/10792689
# REOF = Real End Of File because the script already have EOF
# Quoting of REOF comes from: http://stackoverflow.com/a/8994243
cat << 'REOF' > /home/mountInstanceStore.sh
#!/bin/bash

# This script formats and mounts all available Instance Store devices

##### Variables
devices=( )

##### Functions

function add_device
{
    devices=( "${devices[@]}" $1 )
}

function check_device
{
    if [ -e /dev/$1 ]; then
        add_device $1
    fi
}

function check_devices
{
    # If these lines are added/removed, make sure to check the sed line dealing with /etc/fstab too.
    check_device xvdb
    check_device xvdc
    check_device xvdd
    check_device xvde
    check_device xvdf
    check_device xvdg
    check_device xvdh
    check_device xvdi
    check_device xvdj
    check_device xvdk
}

function print_devices
{
    for device in "${devices[@]}"
    do
        echo Found device $device
    done
}

function do_mount
{
    echo Mounting device $1 on $2
fdisk $1 << EOF
n
p
1



w
EOF
# format!
mkfs -t ext4 $1

if [ ! -e $2 ]; then
    mkdir $2
fi

mount $1 $2

echo "$1   $2        ext4    defaults,nobootwait,comment=cloudconfig          0 2" >> /etc/fstab

}

function mount_devices
{
    for (( i = 0 ; i < ${#devices[@]} ; i++ ))
    do
        if [ $i -eq 0 ]; then
            mountTarget=/home/ubuntu
            # One of the devices may have been mounted.
            umount /mnt 2>/dev/null
        else
            mountTarget=/mnt$(($i+1))
        fi
        do_mount /dev/${devices[$i]} $mountTarget
    done
}


##### Main

check_devices
print_devices
mount_devices
REOF

bash /home/mountInstanceStore.sh

# Remove existing lines involving possibly-mounted devices
# r3.large with 1 instance-store does not mount it.
# c3.large with 2 instance-stores only mounts the first one.
sed -i '/\/dev\/xvd[b-k][ \t]*\/mnt[0-9]*[ \t]*auto[ \t]*defaults,nobootwait,comment=cloudconfig[ \t]*0[ \t]*2/d' /etc/fstab

sudo chown ubuntu:ubuntu /home/ubuntu/
mkdir /home/ubuntu/.ssh/
sudo chown ubuntu:ubuntu /home/ubuntu/.ssh/

# Move ubuntu user dir files back to its home directory which is now mounted on the instance store.
cp -pRP /ubuntuUser-old/.bash_logout /home/ubuntu/.bash_logout
cp -pRP /ubuntuUser-old/.bashrc /home/ubuntu/.bashrc
cp -pRP /ubuntuUser-old/.profile /home/ubuntu/.profile
cp -pRP /ubuntuUser-old/authorized_keys /home/ubuntu/.ssh/authorized_keys
rm -rf /ubuntuUser-old

# -----------------------------------------------------------------------------

# Essential Packages
# Without this ppa, git 1.9.1 is installed, but it sometimes leaves a hung git-remote-https process after cloning
add-apt-repository -y ppa:git-core/ppa  # git 2.x works better
apt-get --yes --quiet update
apt-get --yes --quiet dist-upgrade
apt-get --yes --quiet build-dep firefox
# Retrieved on 2015-08-07: http://hg.mozilla.org/mozilla-central/file/461fc0a6a130/python/mozboot/mozboot/debian.py
apt-get --yes --quiet install autoconf2.13 build-essential ccache mercurial python-dev python-setuptools unzip uuid zip
apt-get --yes --quiet install libasound2-dev libcurl4-openssl-dev libdbus-1-dev libdbus-glib-1-dev libgconf2-dev
apt-get --yes --quiet install libgstreamer0.10-dev libgstreamer-plugins-base0.10-dev libgtk2.0-dev libgtk-3-dev
apt-get --yes --quiet install libiw-dev libnotify-dev libpulse-dev libxt-dev mesa-common-dev python-dbus
apt-get --yes --quiet install yasm xvfb
apt-get --yes --quiet install cmake curl gdb git openssh-server screen silversearcher-ag vim
apt-get --yes --quiet install lib32z1 gcc-multilib g++-multilib  # For compiling 32-bit in 64-bit OS
apt-get --yes --quiet install valgrind libc6-dbg # Needed for Valgrind
apt-get --yes --quiet install mailutils mdadm
apt-get --yes --quiet install xserver-xorg xsel maven openjdk-7-jdk python-virtualenv

# -----------------------------------------------------------------------------

su ubuntu

# Set up deployment keys for funfuzz
@import(userdata/keys/github.funfuzz.sh)@

sudo chown ubuntu:ubuntu /home/ubuntu/.bashrc


# Get the fuzzing harness
sudo -u ubuntu git clone https://github.com/MozillaSecurity/lithium /home/ubuntu/lithium
sudo -u ubuntu git clone https://github.com/MozillaSecurity/funfuzz /home/ubuntu/funfuzz
@import(userdata/misc-funfuzz/location.sh)@

# Populate Mercurial settings.
cat << EOF > /home/ubuntu/.hgrc
[ui]
merge = internal:merge
ssh = ssh -C -v

[extensions]
mq =
progress =
purge =
rebase =

[hostfingerprints]
hg.mozilla.org = af:27:b9:34:47:4e:e5:98:01:f6:83:2b:51:c9:aa:d8:df:fb:1a:27
EOF

sudo chown ubuntu:ubuntu /home/ubuntu/.hgrc

# Download mozilla-central's Mercurial bundle.
sudo -u ubuntu wget -P /home/ubuntu https://ftp.mozilla.org/pub/mozilla.org/firefox/bundles/mozilla-central.hg

# Set up m-c in ~/trees/
sudo -u ubuntu mkdir /home/ubuntu/trees/
sudo -u ubuntu hg --cwd /home/ubuntu/trees/ init mozilla-central

cat << EOF > /home/ubuntu/trees/mozilla-central/.hg/hgrc
[paths]

default = https://hg.mozilla.org/mozilla-central

EOF

sudo chown ubuntu:ubuntu /home/ubuntu/trees/mozilla-central/.hg/hgrc

# Update m-c repository.
sudo -u ubuntu hg -R /home/ubuntu/trees/mozilla-central/ unbundle /home/ubuntu/mozilla-central.hg
sudo -u ubuntu hg -R /home/ubuntu/trees/mozilla-central/ up -C default
sudo -u ubuntu hg -R /home/ubuntu/trees/mozilla-central/ pull
sudo -u ubuntu hg -R /home/ubuntu/trees/mozilla-central/ up -C default

sudo -u ubuntu rm /home/ubuntu/mozilla-central.hg

# Install virtualenv to get boto.
sudo -u ubuntu virtualenv /home/ubuntu/trees/funfuzz-python
sudo -u ubuntu /home/ubuntu/trees/funfuzz-python/bin/pip install boto

cat << EOF > /etc/cron.d/funfuzz
SHELL=/bin/bash
#PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games
MAILTO=gkwong@mozilla.com
#USER=ubuntu
#LOGNAME=ubuntulog
#HOME=/home/ubuntu
@reboot ubuntu /home/ubuntu/trees/funfuzz-python/bin/python -u /home/ubuntu/funfuzz/loopBot.py -b "--random" -t "js" --target-time 28800 | tee /home/ubuntu/log-loopBotPy.txt
EOF

sudo chown root:root /etc/cron.d/funfuzz

##############

# Overwrite CloudInit's configuration setup on (re)boot
cat << EOF > /home/ubuntu/overwriteCloudInitConfig.sh
# Make sure coredumps have the pid appended
echo '1' > /proc/sys/kernel/core_uses_pid

# Edit ~/.bashrc
cat << REOF >> /home/ubuntu/.bashrc

ulimit -c unlimited

# Expand bash shell history length
export HISTTIMEFORMAT="%h %d %H:%M:%S "
HISTSIZE=10000

# Modify bash prompt
export PS1="[\u@\h \d \t \W ] $ "

export LD_LIBRARY_PATH=.

ccache -M 4G
REOF
EOF

cat << EOF > /etc/cron.d/overwriteCloudInitConfigOnBoot
SHELL=/bin/bash
MAILTO=gkwong@mozilla.com
@reboot root /usr/bin/env bash /home/ubuntu/overwriteCloudInitConfig.sh
EOF

##############

sudo reboot
