#!/bin/bash -ex

@import(userdata/common.sh)@

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
pip -q install -r requirements.txt

# Checkout Peach Pits
rm -rf Pits
retry git clone -v --depth 1 git@pits:MozillaSecurity/pits.git

# Checkout script for fetching S3
wget https://gist.githubusercontent.com/posidron/41cb0f276c317ed77264/raw/b3dea77ca22d4040540ce7776f55796e1a2f0dd9/peachbot.py
python userdata.py -sync

# Checkout and setup FuzzManager
retry git clone -v --depth 1 https://github.com/MozillaSecurity/FuzzManager.git Peach/Utilities/FuzzManager
pip install -r Peach/Utilities/FuzzManager/requirements.txt

@import(userdata/loggers/fuzzmanager.sh)@
@import(userdata/loggers/fuzzmanager.binary.sh)@


# Ensure proper permissions
chown -R ubuntu:ubuntu /home/ubuntu


# Example:
# ./laniakea.py -create-on-demand -image-args min_count=1 max_count=1 -tags Name=peach -userdata userdata/peach.sh -userdata-macros TARGET_PIT=pits/targets/laniakea/firefox.xml FUZZING_PIT=pits/files/mp4/fmp4.xml FILE_SAMPLE_PATH=./fuzzdata/samples/mp4

su -c "screen -t peach -dmS peach xvfb-run python ./peach.py -target @TARGET_PIT@ -pit @FUZZING_PIT@ -macro FileSampleMaxFileSize=-1 Strategy=rand.RandomMutationStrategy StrategyParams=SwitchCount=1000 MaxFieldsToMutate=$(($RANDOM % 50)) FileSamplePath=@FILE_SAMPLE_PATH@ WebSocketTemplate=@WEBSOCKET_TEMPLATE@ DataModel=@DATA_MODEL@" ubuntu
