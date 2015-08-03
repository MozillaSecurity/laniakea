#!/bin/bash -ex

@import(userdata/common.sh)@

# Essential Packages

# The following packages are part of the FuzzingOS base image:
#sudo apt-get --yes --quiet update
#sudo apt-get --yes --quiet upgrade
#sudo apt-get --yes --quiet build-dep firefox
#sudo apt-get --yes --quiet install python python-pip python-dev git mercurial s3cmd

# Peach
#sudo apt-get --yes --quiet install libxml2-dev libxslt1-dev lib32z1-dev xterm
#sudo pip install Twisted==14.0.0 lxml==3.3.5 psutil==2.1.1 pyasn1==0.1.7 tlslite==0.4.6

# FuzzManager
#sudo pip install Django==1.7.1 numpy==1.9.1 djangorestframework==2.4.4 requests>=2.5.0 lockfile>=0.8


# Add GitHub as a known host
ssh-keyscan github.com >> /root/.ssh/known_hosts

# Setup deploy keys for Peach
@import(userdata/keys/github.peach.sh)@


cd /home/ubuntu


# Target desscription for Firefox
@import(userdata/targets/mozilla-inbound-linux64-asan.sh)@


# Checkout Peach
retry git clone -v --depth 1 git@peach:MozillaSecurity/peach.git
cd peach

# Install Peach dependencies
pip -q install -r requirements.txt

# Checkout Peach Pits
rm -rf Pits
retry git clone -v --depth 1 git@pits:MozillaSecurity/pits.git Pits

# Download PeachBot
wget https://gist.githubusercontent.com/posidron/41cb0f276c317ed77264/raw/f37d524a1e055d75aa68f7740340e65102288169/peachbot.py
chmod a+x peachbot.py

# Checkout fuzzing resources
git clone https://github.com/MozillaSecurity/fuzzdata

# Checkout and setup FuzzManager
retry git clone -v --depth 1 https://github.com/MozillaSecurity/FuzzManager.git Peach/Utilities/FuzzManager
pip install -r Peach/Utilities/FuzzManager/requirements.txt

@import(userdata/loggers/fuzzmanager.sh)@
@import(userdata/loggers/fuzzmanager.binary.sh)@


# Ensure proper permissions
chown -R ubuntu:ubuntu /home/ubuntu


# Run FuzzingBot as user "ubuntu"
su -c "screen -t peach -dmS peach xvfb-run python peachbot.py -tasks 50 -testcases 50000 -data . -pits Pits/" ubuntu
