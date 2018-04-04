#! /bin/bash -ex
# Be in ~/trees/laniakea directory, be sure @import directories are present.
# python -u -m laniakea ec2 -region=us-east-1 -images ~/images.json -create-on-demand -tags Name=funfuzz-1604-ondemand-201804 -image-name funfuzz-ondemand-ebs -ebs-volume-delete-on-termination -ebs-size 96 -root-device-type ebs -userdata laniakea/userdata/ec2/funfuzz.sh
# Stop the instance, create an AMI, copy the AMI, then update EC2SpotManager
export DEBIAN_FRONTEND=noninteractive  # Bypass ncurses configuration screens

date
sleep 10  # EC2 takes some time to be able to go online
# Essential Packages
# PPAs for newest nodejs, Git, Rust, GCC 6, LLVM/Clang 6
curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -  # For nodejs
add-apt-repository -y ppa:git-core/ppa  # Git PPA needed to get latest security updates
add-apt-repository -y ppa:ubuntu-mozilla-security/rust-next
add-apt-repository -y ppa:ubuntu-toolchain-r/test
# Fingerprint: 6084 F3CF 814B 57C1 CF12 EFD5 15CF 4D18 AF4F 7421
wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key|sudo apt-key add -
echo "deb http://apt.llvm.org/xenial/ llvm-toolchain-xenial-6.0 main" >> /etc/apt/sources.list
echo "deb-src http://apt.llvm.org/xenial/ llvm-toolchain-xenial-6.0 main" >> /etc/apt/sources.list

apt-get --yes --quiet update
apt-get --yes --quiet dist-upgrade
# Check using `hg --cwd ~/trees/mozilla-central/ diff -r 781485c695e1:00bdc9451be6 python/mozboot/mozboot/debian.py`
# Retrieved on 2018-04-03: https://hg.mozilla.org/mozilla-central/file/00bdc9451be6/python/mozboot/mozboot/debian.py
apt-get --yes --quiet install autoconf2.13 build-essential ccache python-dev python-pip python-setuptools unzip uuid zip
apt-get --yes --quiet install libasound2-dev libcurl4-openssl-dev libdbus-1-dev libdbus-glib-1-dev libgconf2-dev
apt-get --yes --quiet install libgtk2.0-dev libgtk-3-dev libpulse-dev libx11-xcb-dev libxt-dev
apt-get --yes --quiet install nodejs python-dbus yasm xvfb
apt-get --yes --quiet install cmake curl gdb git openssh-client openssh-server screen vim
apt-get --yes --quiet install gcc-6 g++-6
apt-get --yes --quiet install lib32z1 gcc-6-multilib g++-6-multilib  # For compiling 32-bit in 64-bit OS

# Switch to GCC 6
update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-5 10
update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-6 20
update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-5 10
update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-6 20

update-alternatives --install /usr/bin/cc cc /usr/bin/gcc 30
update-alternatives --set cc /usr/bin/gcc
update-alternatives --install /usr/bin/c++ c++ /usr/bin/g++ 30
update-alternatives --set c++ /usr/bin/g++

# Needed for Valgrind and for compiling with clang, along with llvm-symbolizer
apt-get --yes --quiet install valgrind libc6-dbg
# Install rust
apt-get --yes --quiet install cargo rustc

# Install LLVM/Clang 6
apt-get --yes --quiet install clang-6.0 clang-tools-6.0 clang-6.0-doc libclang-common-6.0-dev libclang-6.0-dev
apt-get --yes --quiet install libclang1-6.0 libclang1-6.0-dbg libllvm6.0 libllvm6.0-dbg
apt-get --yes --quiet install lldb-6.0 llvm-6.0 llvm-6.0-dev llvm-6.0-doc llvm-6.0-examples llvm-6.0-runtime 
apt-get --yes --quiet install clang-format-6.0 python-clang-6.0 lld-6.0 libfuzzer-6.0-dev

LLVMSYMBOLIZER="/usr/bin/llvm-symbolizer-6.0"  # Update this number whenever Clang is updated
LLVMSYMBOLIZER_DEST="/usr/bin/llvm-symbolizer"
if [ -f $LLVMSYMBOLIZER ];
then
    echo "Creating $LLVMSYMBOLIZER_DEST symlink to file located at: $LLVMSYMBOLIZER"
    ln -s $LLVMSYMBOLIZER $LLVMSYMBOLIZER_DEST
else
    echo "WARNING: File $LLVMSYMBOLIZER does not exist."
fi
apt-get --yes --quiet autoremove
apt-get --yes --quiet upgrade

# -----------------------------------------------------------------------------
date

# Install ripgrep as the ubuntu user
sudo -u ubuntu cargo install ripgrep

cat << EOF > /home/ubuntu/.ssh/config
Host *
StrictHostKeyChecking no

EOF
chown -R ubuntu:ubuntu /home/ubuntu/.ssh

chown ubuntu:ubuntu /home/ubuntu/.bashrc

# Get the fuzzing harness
sudo -u ubuntu git clone https://github.com/MozillaSecurity/autobisect /home/ubuntu/autobisect
sudo -u ubuntu git clone https://github.com/MozillaSecurity/ffpuppet /home/ubuntu/ffpuppet
sudo -u ubuntu git clone https://github.com/MozillaSecurity/octo /home/ubuntu/octo
sudo -u ubuntu git clone https://github.com/MozillaSecurity/funfuzz /home/ubuntu/funfuzz

# Get more fuzzing prerequisites
sudo -u ubuntu pip install --user --upgrade pip setuptools
sudo -u ubuntu pip install --user --upgrade mercurial

# Get supporting fuzzing libraries via pip
sudo -u ubuntu pip install --user --upgrade /home/ubuntu/funfuzz

# Populate FuzzManager settings
@import(laniakea/userdata/ec2/misc-funfuzz/fmsettings.sh)@

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

chown ubuntu:ubuntu /home/ubuntu/.hgrc

# Clone m-c repository.
date
sudo -u ubuntu hg clone https://hg.mozilla.org/mozilla-central /home/ubuntu/trees/mozilla-central
sudo -u ubuntu hg clone https://hg.mozilla.org/releases/mozilla-beta /home/ubuntu/trees/mozilla-beta
sudo -u ubuntu hg clone https://hg.mozilla.org/releases/mozilla-esr60 /home/ubuntu/trees/mozilla-esr60
date

cat << EOF > /home/ubuntu/funfuzzCronjob
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games
USER=ubuntu
LOGNAME=ubuntulog
HOME=/home/ubuntu
@reboot ubuntu sleep 80 ; git -C /home/ubuntu/funfuzz pull --rebase --tags ; pip install --user --upgrade /home/ubuntu/funfuzz ; python -u -m funfuzz.loop_bot -b "--random" --target-time 28800 | tee /home/ubuntu/log-loopBotPy.txt
EOF

chown root:root /home/ubuntu/funfuzzCronjob

##############

# Overwrite CloudInit's configuration setup on (re)boot
cat << EOF > /home/ubuntu/overwriteCloudInitConfig.sh
# Make sure coredumps have the pid appended
echo '1' > /proc/sys/kernel/core_uses_pid

# Sometimes the above line is insufficient
echo 'kernel.core_uses_pid = 1' >> /etc/sysctl.conf

# Edit ~/.bashrc if it has not yet been done so
if [[ \$(tac /home/ubuntu/.bashrc | egrep -m 1 .) != 'ccache -M 8G' ]]; then
cat << 'REOF' >> /home/ubuntu/.bashrc

ulimit -c unlimited

# Expand bash shell history length
export HISTTIMEFORMAT="%h %d %H:%M:%S "
HISTSIZE=10000

# Modify bash prompt
export PS1="[\u@\h \d \t \W ] $ "

export LD_LIBRARY_PATH=.
export ASAN_SYMBOLIZER_PATH=/usr/bin/llvm-symbolizer

ccache -M 8G
REOF
fi
EOF

cat << EOF > /etc/cron.d/overwriteCloudInitConfigOnBoot
SHELL=/bin/bash
@reboot root /usr/bin/env bash /home/ubuntu/overwriteCloudInitConfig.sh
EOF

##############
date
reboot
