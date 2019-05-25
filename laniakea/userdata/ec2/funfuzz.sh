#! /bin/bash -ex
# Be in ~/trees/laniakea directory, be sure @import directories are present.
# python3 -u -m laniakea ec2 -region=us-east-1 -images ~/amazon.json -create-on-demand -tags Name=funfuzz-1804-ondemand-201905b -image-name funfuzz-ondemand-ebs -ebs-volume-delete-on-termination -ebs-size 96 -root-device-type ebs -userdata laniakea/userdata/ec2/funfuzz.sh
# Stop the instance, create an AMI, copy the AMI, then update EC2SpotManager
export DEBIAN_FRONTEND=noninteractive  # Bypass ncurses configuration screens

date
sleep 10  # EC2 takes some time to be able to go online
# Essential Packages
# PPAs for newest nodejs, Git, LLVM/Clang
curl -sL https://deb.nodesource.com/setup_10.x | sudo -E bash -  # For nodejs
add-apt-repository -y ppa:git-core/ppa  # Git PPA needed to get latest security updates
add-apt-repository -y ppa:x4121/ripgrep
#add-apt-repository -y ppa:ubuntu-toolchain-r/test
# Fingerprint: 6084 F3CF 814B 57C1 CF12 EFD5 15CF 4D18 AF4F 7421
# LLVM/Clang is now in Ubuntu's repositories
# wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key|sudo apt-key add -
# echo "deb http://apt.llvm.org/bionic/ llvm-toolchain-bionic-6.0 main" >> /etc/apt/sources.list
# echo "deb-src http://apt.llvm.org/bionic/ llvm-toolchain-bionic-6.0 main" >> /etc/apt/sources.list

apt-get --yes --quiet update
apt-get --yes --quiet dist-upgrade
# Check using `hg --cwd ~/trees/mozilla-central/ diff -r 7e40e33da3da:d551d37b9ad0 python/mozboot/mozboot/debian.py`
# Retrieved on 2019-05-23: https://hg.mozilla.org/mozilla-central/file/d551d37b9ad0/python/mozboot/mozboot/debian.py
apt-get --yes --quiet install autoconf2.13 build-essential ccache python-dev python-pip python-setuptools \
    unzip uuid zip \
    python3-pip python3-setuptools \
    libasound2-dev libcurl4-openssl-dev libdbus-1-dev libdbus-glib-1-dev libgconf2-dev \
    libgtk2.0-dev libgtk-3-dev libpulse-dev libx11-xcb-dev libxt-dev \
    nasm nodejs python-dbus yasm xvfb \
    aria2 cmake curl gdb git openssh-client openssh-server screen ripgrep vim
apt-get --yes --quiet install libc6-dev-i386 g++-multilib  # For compiling 32-bit in 64-bit OS

# Needed for Valgrind and for compiling with clang, along with llvm-symbolizer
apt-get --yes --quiet install valgrind libc6-dbg

# Install LLVM/Clang
apt-get --yes --quiet install clang-7 clang-tools-7 clang-7-doc libclang-common-7-dev libclang-7-dev \
    libclang1-7 libllvm7 \
    lldb-7 llvm-7 llvm-7-dev llvm-7-doc llvm-7-examples llvm-7-runtime \
    clang-format-7 python-clang-7 lld-7 libfuzzer-7-dev

# Switch to LLVM/Clang
update-alternatives --install /usr/bin/clang clang /usr/bin/clang-7 8
update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-7 8
update-alternatives --install /usr/bin/lldb lldb /usr/bin/lldb-7 8
update-alternatives --install /usr/bin/llvm-config llvm-config /usr/bin/llvm-config-7 8
update-alternatives --install /usr/bin/llvm-symbolizer llvm-symbolizer /usr/bin/llvm-symbolizer-7 8

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
sudo -u ubuntu git clone https://github.com/MozillaSecurity/ffpuppet /home/ubuntu/ffpuppet
sudo -u ubuntu git clone https://github.com/MozillaSecurity/octo /home/ubuntu/octo
sudo -u ubuntu git clone https://github.com/MozillaSecurity/funfuzz /home/ubuntu/funfuzz

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
wget -O- https://git.io/fxxh4 | sudo -u ubuntu bash -s -- /releases/ mozilla-beta /home/ubuntu/trees
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
