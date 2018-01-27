#!/bin/bash -ex

@import(userdata/common.sh)@

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
retry wget https://gist.githubusercontent.com/posidron/f9d00c2387aaac15f8ea/raw/347d03bffbf1ade03487b52d9f5c195ead4a06c8/userdata.py
python userdata.py -sync

# 3 - Checkout Quokka harness
retry git clone -v --depth 1 https://github.com/MozillaSecurity/quokka.git

# 4 - Checkout Dharma
retry git clone -v --depth 1 https://github.com/MozillaSecurity/dharma.git
cd dharma/dharma
rm -rf grammars

# 5 - Checkout private Dharma grammars
retry git clone -v --depth 1 git@dharma-grammars:MozillaSecurity/dharma-grammars.git grammars

# 6 - Checkout Dharma bot
retry wget https://gist.githubusercontent.com/posidron/f6ccad252f1045226c97/raw/172a7269557bee79e48ec7cece64a2451eb4db93/dharmabot.py
chmod a+x dharmabot.py


# Ensure proper permissions
chown -R ubuntu:ubuntu /home/ubuntu

cd /home/ubuntu/dharma/dharma
su -c "screen -t dharma -dmS dharma ./dharmabot.py --input_dir /home/ubuntu/Resources" ubuntu

cd /home/ubuntu/quokka
su -c "screen -t quokka -dmS quokka xvfb-run -a ./quokka.py -plugin configs/firefox-aws.json -conf-args environ.ASAN_SYMBOLIZE=/home/ubuntu/firefox/llvm-symbolizer -conf-vars params=file://$TARGET"
