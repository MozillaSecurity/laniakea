#! /bin/bash -ex
# Be in ~/trees/laniakea directory, be sure @import directories are present.
# Run `diff arm64-funfuzz.sh funfuzz.sh` to find out the differences
# Stop the instance, create an AMI, copy the AMI, then update EC2SpotManager
export DEBIAN_FRONTEND=noninteractive  # Bypass ncurses configuration screens

date
sleep 10  # EC2 takes some time to be able to go online
# Essential Packages
# PPAs for newest nodejs, Git, LLVM/Clang
curl -sL https://deb.nodesource.com/setup_12.x | sudo -E bash -  # For nodejs
add-apt-repository -y ppa:git-core/ppa  # Git PPA needed to get latest security updates
add-apt-repository -y ppa:x4121/ripgrep

apt-get --yes --quiet update
apt-get --yes --quiet dist-upgrade
# Check using `hg --cwd ~/trees/mozilla-central/ diff -r b4b26439b03d:95ad10e13fb1 python/mozboot/mozboot/debian.py`
# Retrieved on 2019-08-23: https://hg.mozilla.org/mozilla-central/file/95ad10e13fb1/python/mozboot/mozboot/debian.py
apt-get --yes --quiet install autoconf2.13 build-essential ccache python-dev python-pip python-setuptools \
    unzip uuid zip \
    python3-pip python3-setuptools \
    libasound2-dev libcurl4-openssl-dev libdbus-1-dev libdbus-glib-1-dev \
    libgtk2.0-dev libgtk-3-dev libpulse-dev libx11-xcb-dev libxt-dev \
    nasm nodejs python-dbus yasm xvfb \
    aria2 cmake curl gdb git openssh-client openssh-server screen ripgrep vim
# ARM64 does not have libc6-dev-i386 nor g++-multilib
# apt-get --yes --quiet install libc6-dev-i386 g++-multilib  # For compiling 32-bit in 64-bit OS

# After EC2 image creation, remember to first try out `rr record ls`
# rr requirements from https://github.com/mozilla/rr/wiki/Building-And-Installing
# Commented out since rr does not yet seem to support aarch64 on a1.4xlarge as of 2019-08-23
# Note that ARM64 does *NOT* have g++-multilib
# apt-get --yes --quiet install ccache cmake make gdb pkg-config coreutils python3-pexpect manpages-dev git \
#     ninja-build capnproto libcapnp-dev
# apt-get --yes --quiet install zstd  # For pernosco-submit

# Needed for Valgrind and for compiling with clang, along with llvm-symbolizer
apt-get --yes --quiet install valgrind libc6-dbg

# Install LLVM/Clang
apt-get --yes --quiet install clang-8 clang-tools-8 clang-8-doc libclang-common-8-dev libclang-8-dev \
    libclang1-8 libllvm8 \
    lldb-8 llvm-8 llvm-8-dev llvm-8-doc llvm-8-examples llvm-8-runtime \
    clang-format-8 python-clang-8 lld-8 libfuzzer-8-dev

# Switch to LLVM/Clang
update-alternatives --install /usr/bin/clang clang /usr/bin/clang-8 8
update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-8 8
update-alternatives --install /usr/bin/lldb lldb /usr/bin/lldb-8 8
update-alternatives --install /usr/bin/llvm-config llvm-config /usr/bin/llvm-config-8 8
update-alternatives --install /usr/bin/llvm-symbolizer llvm-symbolizer /usr/bin/llvm-symbolizer-8 8

apt-get --yes --quiet autoremove
apt-get --yes --quiet upgrade

# Install Rust using rustup
sudo -u ubuntu curl https://sh.rustup.rs -sSf | sudo -u ubuntu sh -s -- -y
sudo -u ubuntu /home/ubuntu/.cargo/bin/rustup update stable
sudo -u ubuntu /home/ubuntu/.cargo/bin/rustup target add i686-unknown-linux-gnu
sudo -u ubuntu /home/ubuntu/.cargo/bin/rustup --version
sudo -u ubuntu /home/ubuntu/.cargo/bin/rustc --version

# -----------------------------------------------------------------------------
date

cat << EOF > /home/ubuntu/.ssh/config
Host *
StrictHostKeyChecking no

EOF
chown -R ubuntu:ubuntu /home/ubuntu/.ssh

chown ubuntu:ubuntu /home/ubuntu/.bashrc

# Get the fuzzing harness
sudo -u ubuntu git clone https://github.com/MozillaSecurity/autobisect /home/ubuntu/autobisect
sudo -u ubuntu git clone https://github.com/WebAssembly/binaryen /home/ubuntu/binaryen
sudo -u ubuntu git clone https://github.com/MozillaSecurity/octo /home/ubuntu/octo
sudo -u ubuntu git clone https://github.com/MozillaSecurity/funfuzz /home/ubuntu/funfuzz

# Compile binaryen on ARM64 Linux due to https://github.com/WebAssembly/binaryen/issues/1615
sudo -u ubuntu git -C /home/ubuntu/binaryen/ checkout "version_$(grep -m1 '^BINARYEN_VERSION = ' /home/ubuntu/funfuzz/src/funfuzz/js/with_binaryen.py | cut -c20-)"
pushd /home/ubuntu/binaryen/
sudo -u ubuntu cmake .
sudo -u ubuntu make -j4
popd
sudo -u ubuntu mkdir -p "/home/ubuntu/shell-cache/binaryen-version_$(grep -m1 '^BINARYEN_VERSION = ' /home/ubuntu/funfuzz/src/funfuzz/js/with_binaryen.py | cut -c20-)"
sudo -u ubuntu cp /home/ubuntu/binaryen/bin/* "/home/ubuntu/shell-cache/binaryen-version_$(grep -m1 '^BINARYEN_VERSION = ' /home/ubuntu/funfuzz/src/funfuzz/js/with_binaryen.py | cut -c20-)"
if [ ! -e "/home/ubuntu/shell-cache/binaryen-version_$(grep -m1 '^BINARYEN_VERSION = ' /home/ubuntu/funfuzz/src/funfuzz/js/with_binaryen.py | cut -c20-)/wasm-opt" ]; then
    echo "wasm-opt does not exist in the shell-cache binaryen folder"
else
    echo "wasm-opt does exist in the shell-cache binaryen folder"
fi

# Get more fuzzing prerequisites - have to install as root, else `hg` is not found by the rest of this script
python -m pip install --upgrade pip setuptools virtualenv
python -m pip install --upgrade pip setuptools
python -m pip install --upgrade mercurial  # Mercurial only supports Python 2 for now
python3 -m pip install --upgrade pip setuptools virtualenv
python3 -m pip install --upgrade future-breakpoint jsbeautifier

# Get supporting fuzzing libraries via pip, funfuzz will be used as the "ubuntu" user later
pushd /home/ubuntu/funfuzz/  # For requirements.txt to work properly, we have to be in the repository directory
sudo -u ubuntu python3 -m pip install --user --upgrade -r /home/ubuntu/funfuzz/requirements.txt
popd

# # Get rr from master at https://github.com/mozilla/rr
# sudo -u ubuntu git clone https://github.com/mozilla/rr /home/ubuntu/rr
# sudo -u ubuntu mkdir /home/ubuntu/rr/obj
# pushd /home/ubuntu/rr/obj
# CC=clang CXX=clang++ sudo -u ubuntu cmake -G Ninja ..
# sudo -u ubuntu cmake --build .
# cmake --build . --target install
# popd
# echo 'kernel.perf_event_paranoid=1' > '/etc/sysctl.d/51-enable-perf-events.conf'

# # For pernosco-submit
# sudo -u ubuntu git clone https://github.com/Pernosco/pernosco-submit /home/ubuntu/pernosco-submit
# sudo -u ubuntu python3 -m pip install --user --upgrade awscli

# Populate FuzzManager settings
@import(misc-funfuzz/fmsettings.sh)@

# Populate Mercurial settings.
cat << EOF > /home/ubuntu/.hgrc
[ui]
username = gkw
merge = internal:merge
ssh = ssh -C -v

[extensions]
mq =
progress =
purge =
rebase =
EOF

chown ubuntu:ubuntu /home/ubuntu/.hgrc

# Add vimrc for Bionic
cat << EOF > /home/ubuntu/.vimrc
:syntax enable
syntax on
set number
set ruler
set nocompatible
set bs=2
fixdel
set nowrap
set tabstop=4
set autoindent
set term=xterm
set smartindent
set showmode showcmd
set shiftwidth=4
set expandtab
set backspace=indent,eol,start
set hls
au BufNewFile,BufRead *.* exec 'match Error /\%119v/'
set paste
EOF

chown ubuntu:ubuntu /home/ubuntu/.vimrc

# Clone repositories using get_hg_repo.sh
date
mkdir -p /home/ubuntu/trees/
chown ubuntu:ubuntu /home/ubuntu/trees
pushd /home/ubuntu/trees/
wget -O- https://git.io/fxxh4 | sudo -u ubuntu bash -s -- / mozilla-central /home/ubuntu/trees
popd
date

cat << EOF > /home/ubuntu/funfuzzCronjob
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/home/ubuntu/.cargo/bin:/home/ubuntu/.local/bin
USER=ubuntu
LOGNAME=ubuntulog
HOME=/home/ubuntu
@reboot ubuntu sleep 80 ; git -C /home/ubuntu/funfuzz pull --rebase --tags ; pushd /home/ubuntu/funfuzz ; python3 -m pip install --user --upgrade -r /home/ubuntu/funfuzz/requirements.txt ; popd ; python3 -u -m funfuzz.loop_bot -b "--random" --target-time 28800 | tee /home/ubuntu/log-loopBotPy.txt
EOF

chown root:root /home/ubuntu/funfuzzCronjob

##############

# When moving this portion to Orion, put it in userdata
# Overwrite CloudInit's configuration setup on (re)boot
cat << EOF > /home/ubuntu/overwriteCloudInitConfig.sh
# Make sure coredumps have the pid appended
echo '1' > /proc/sys/kernel/core_uses_pid

# Sometimes the above line is insufficient
echo 'kernel.core_uses_pid = 1' >> /etc/sysctl.conf

# Disable apport
sed -i 's/enabled=1/enabled=0/g' /etc/default/apport  # On EC2, sometimes this isn't enough
/etc/init.d/apport stop  # Ensure it has been stopped forcibly

# Edit ~/.bashrc if it has not yet been done so
if [[ \$(tac /home/ubuntu/.bashrc | egrep -m 1 .) != 'ccache -M 12G' ]]; then
cat << 'REOF' >> /home/ubuntu/.bashrc

ulimit -c unlimited

# Expand bash shell history length
export HISTTIMEFORMAT="%h %d %H:%M:%S "
HISTSIZE=10000

# Modify bash prompt
export PS1="[\u@\h \d \t \W ] $ "

export LD_LIBRARY_PATH=.
export ASAN_OPTIONS=detect_leaks=1,
export LSAN_OPTIONS=max_leaks=1,
export ASAN_SYMBOLIZER_PATH=/usr/bin/llvm-symbolizer

PATH=/home/ubuntu/.cargo/bin:/home/ubuntu/.local/bin:$PATH

ccache -M 12G
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
