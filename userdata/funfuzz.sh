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

# List of EC2 instance options: http://aws.amazon.com/ec2/pricing/
# Generally, anything with *4.* (e.g. c4.4xlarge) will be newer and have EBS-only instance storage,
# so if you're using *4.*, comment out the code between:
### STARTMOUNTSSDSTORAGE ### and ### ENDMOUNTSSDSTORAGE ###
# Ideally, use r3.4xlarge for now

### STARTMOUNTSSDSTORAGE ###
# Format and mount all available instance stores.
# Adapted from http://stackoverflow.com/a/10792689
# REOF = Real End Of File because the script already has EOF
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
mkfs -t ext4 $1 << EOF
y
EOF

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
sed -i '/\/dev\/xvd[b-k][0-9]*[ \t]*\/mnt[0-9]*[ \t]*auto[ \t]*defaults,nobootwait,comment=cloudconfig[ \t]*0[ \t]*2/d' /etc/fstab
### ENDMOUNTSSDSTORAGE ###

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

date
# Essential Packages
add-apt-repository -y ppa:git-core/ppa  # Git PPA needed to get latest security updates
apt-get --yes --quiet update
apt-get --yes --quiet dist-upgrade
apt-get --yes --quiet build-dep firefox
# Check using `hg diff -r f3f2fa1d7eed:2ea3d51ba1bb python/mozboot/mozboot/debian.py`
# Retrieved on 2016-07-29: http://hg.mozilla.org/mozilla-central/file/2ea3d51ba1bb/python/mozboot/mozboot/debian.py
apt-get --yes --quiet install autoconf2.13 build-essential ccache python-dev python-pip python-setuptools unzip uuid zip
apt-get --yes --quiet install libasound2-dev libcurl4-openssl-dev libdbus-1-dev libdbus-glib-1-dev libgconf2-dev
apt-get --yes --quiet install libgtk2.0-dev libgtk-3-dev libiw-dev libnotify-dev libpulse-dev libx11-xcb-dev libxt-dev
apt-get --yes --quiet install mesa-common-dev python-dbus yasm xvfb
apt-get --yes --quiet install cmake curl gdb git openssh-client openssh-server python-virtualenv screen silversearcher-ag vim
apt-get --yes --quiet install lib32z1 gcc-multilib g++-multilib  # For compiling 32-bit in 64-bit OS
# Needed for Valgrind and for compiling with clang, along with llvm-symbolizer
apt-get --yes --quiet install valgrind libc6-dbg clang
LLVMSYMBOLIZER="/usr/bin/llvm-symbolizer-3.8"  # Update this number whenever Clang is updated
LLVMSYMBOLIZER_DEST="/usr/bin/llvm-symbolizer"
if [ -f $LLVMSYMBOLIZER ];
then
    echo "Creating $LLVMSYMBOLIZER_DEST symlink to file located at: $LLVMSYMBOLIZER"
    sudo ln -s $LLVMSYMBOLIZER $LLVMSYMBOLIZER_DEST
else
    echo "WARNING: File $LLVMSYMBOLIZER does not exist."
fi
# Needed for DOMFuzz stuff
#apt-get --yes --quiet install xserver-xorg xsel maven openjdk-7-jdk

# -----------------------------------------------------------------------------
date
su ubuntu

cat << EOF > /home/ubuntu/.ssh/config
Host *
StrictHostKeyChecking no
EOF
sudo chown -R ubuntu:ubuntu /home/ubuntu/.ssh

sudo chown ubuntu:ubuntu /home/ubuntu/.bashrc

# Get more fuzzing prerequisites
pip install --upgrade pip virtualenv boto mercurial numpy requests

# Get the fuzzing harness
sudo -u ubuntu git clone https://github.com/nth10sd/lithium /home/ubuntu/lithium -b nbp-branch --single-branch
sudo -u ubuntu git clone https://github.com/MozillaSecurity/funfuzz /home/ubuntu/funfuzz
sudo -u ubuntu git clone https://github.com/MozillaSecurity/FuzzManager /home/ubuntu/FuzzManager

# Populate FuzzManager settings
@import(userdata/misc-funfuzz/fmsettings.sh)@

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
EOF

sudo chown ubuntu:ubuntu /home/ubuntu/.hgrc

# Clone m-c repository.
date
sudo -u ubuntu hg clone https://hg.mozilla.org/mozilla-central /home/ubuntu/trees/mozilla-central
date
sudo -u ubuntu hg clone https://hg.mozilla.org/releases/mozilla-aurora/ /home/ubuntu/trees/mozilla-aurora
date
sudo -u ubuntu hg clone https://hg.mozilla.org/releases/mozilla-esr45/ /home/ubuntu/trees/mozilla-esr45
date

cat << EOF > /etc/cron.d/funfuzz
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games
USER=ubuntu
LOGNAME=ubuntulog
HOME=/home/ubuntu
@reboot ubuntu python -u /home/ubuntu/funfuzz/loopBot.py -b "--random" -t "js" --target-time 28800 | tee /home/ubuntu/log-loopBotPy.txt
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
export ASAN_SYMBOLIZER_PATH=/usr/bin/llvm-symbolizer

ccache -M 4G
REOF
EOF

cat << EOF > /etc/cron.d/overwriteCloudInitConfigOnBoot
SHELL=/bin/bash
@reboot root /usr/bin/env bash /home/ubuntu/overwriteCloudInitConfig.sh
EOF

##############
date
sudo reboot
