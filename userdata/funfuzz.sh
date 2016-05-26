#! /bin/bash -ex
# Use only *4.* instances or *3.* instances with EBS storage.
export DEBIAN_FRONTEND=noninteractive  # Bypass ncurses configuration screens

# Essential Packages
add-apt-repository -y ppa:git-core/ppa  # Git PPA needed to get latest security updates
apt-get --yes --quiet update
apt-get --yes --quiet dist-upgrade
apt-get --yes --quiet build-dep firefox
# Check using `hg diff -r be593a64d7c6:f3f2fa1d7eed python/mozboot/mozboot/debian.py`
# Retrieved on 2016-05-17: http://hg.mozilla.org/mozilla-central/file/f3f2fa1d7eed/python/mozboot/mozboot/debian.py
apt-get --yes --quiet install autoconf2.13 build-essential ccache python-dev python-pip python-setuptools unzip uuid zip
apt-get --yes --quiet install libasound2-dev libcurl4-openssl-dev libdbus-1-dev libdbus-glib-1-dev libgconf2-dev
apt-get --yes --quiet install libgtk2.0-dev libgtk-3-dev libiw-dev libnotify-dev libpulse-dev libxt-dev
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

su ubuntu

cat << EOF > /home/ubuntu/.ssh/config
Host *
StrictHostKeyChecking no
EOF
sudo chown -R ubuntu:ubuntu /home/ubuntu/.ssh

sudo chown ubuntu:ubuntu /home/ubuntu/.bashrc

# Get more fuzzing prerequisites
pip install --upgrade boto mercurial numpy requests

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
sudo -u ubuntu hg clone https://hg.mozilla.org/mozilla-central /home/ubuntu/trees/mozilla-central
sudo -u ubuntu hg clone https://hg.mozilla.org/releases/mozilla-aurora/ /home/ubuntu/trees/mozilla-aurora
sudo -u ubuntu hg clone https://hg.mozilla.org/releases/mozilla-esr45/ /home/ubuntu/trees/mozilla-esr45

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

sudo reboot
