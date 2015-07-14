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

# Setup deploy keys for Dharma
@import(userdata/keys/github.dharma.grammars.sh)@

cd /home/ubuntu

@import(userdata/targets/mozilla-inbound-linux64-asan.sh)@


# 1 - Checkout and setup FuzzManager
retry git clone -v --depth 1 https://github.com/MozillaSecurity/FuzzManager.git FuzzManager
pip install -r FuzzManager/requirements.txt

@import(userdata/loggers/fuzzmanager.sh)@
@import(userdata/loggers/fuzzmanager.binary.sh)@

# 2 - Checkout script for fetching S3
wget https://gist.githubusercontent.com/posidron/f9d00c2387aaac15f8ea/raw/347d03bffbf1ade03487b52d9f5c195ead4a06c8/userdata.py
python userdata.py -sync

# 3 - Checkout Quokka harness
retry git clone -v --depth 1 https://github.com/MozillaSecurity/quokka.git

# 4 - Checkout Dharma
retry git clone -v --depth 1 https://github.com/MozillaSecurity/dharma.git
cd dharma/dharma
rm -rf grammars

# 5 - Checkout private Dharma grammars
retry git clone -v --depth 1 git@dharma-grammars:MozillaSecurity/dharma-grammars.git grammars


# 6 - Configure Dharma
DHARMA_PATH="/home/ubuntu/dharma/dharma"

export GRAMMAR="$DHARMA_PATH/grammars/canvas2d.dg"
export TEMPLATE="$DHARMA_PATH/grammars/var/templates/html5/default.html"
export TARGET="$DHARMA_PATH/grammars/var/index.html" 

echo '
DharmaConst.VARIANCE_MIN = 1
DharmaConst.VARIANCE_MAX = 1
DharmaConst.VARIANCE_TEMPLATE = "%s"
DharmaConst.MAX_REPEAT_POWER = 12
DharmaConst.LEAF_TRIGGER = 256
DharmaConst.URI_TABLE = {
    "images": "/home/ubuntu/Resources/Samples/jpg/",
    "videos": "/home/ubuntu/Resources/Samples/mp4/",
    "audios": "/home/ubuntu/Resources/Samples/mp3/",
}
' > settings.py

# 7 - Configure Quokka


# Ensure proper permissions
chown -R ubuntu:ubuntu /home/ubuntu

cd /home/ubuntu/dharma/dharma
su -c "screen -t dharma -dmS dharma ./dharma.py -server -grammars $GRAMMAR -template $TEMPLATE" ubuntu

cd /home/ubuntu/quokka
su -c "screen -t quokka -dmS quokka xvfb-run -a ./quokka.py -plugin configs/firefox-aws.json -conf-args environ.ASAN_SYMBOLIZE=/home/ubuntu/firefox/llvm-symbolizer -conf-vars params=file://$TARGET"
