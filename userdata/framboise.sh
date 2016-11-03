#!/bin/bash -ex

# https://help.ubuntu.com/community/CloudInit
# http://www.knowceantech.com/2014/03/amazon-cloud-bootstrap-with-userdata-cloudinit-github-puppet/

# Bash Utilities
function retry {
	for i in {1..5}; do $@ && break || sleep 1; done
}

# Essential Packages

# The following packages are part of the FuzzingOS base image:
#sudo apt-get --yes --quiet update
#sudo apt-get --yes --quiet upgrade
#sudo apt-get --yes --quiet build-dep firefox
#sudo apt-get --yes --quiet install \
#	python python-pip python-dev git mercurial s3cmd

# The following packages are part of the FuzzingOS base image:
sudo apt-get --yes --quiet update
#sudo apt-get --yes --quiet upgrade
#sudo apt-get --yes --quiet build-dep firefox
sudo apt-get --yes --quiet install libgtk-3.0
sudo apt-get --yes --quiet install python3 python3-pip python-dev git

# Add GitHub as a known host
ssh-keyscan github.com >> /root/.ssh/known_hosts

@import(userdata/keys/github.framboise.modules.sh)@

cd /home/ubuntu

# Download ASan build of Firefox
ARTIFACT_NAME="en-US.linux-x86_64-asan.tar.bz2"
TASK_ID=$(wget -q -O - https://index.taskcluster.net/v1/task/gecko.v2.mozilla-inbound.latest.firefox.linux64-asan-opt | python3 -c "import json,sys; print(json.load(sys.stdin)['taskId'])")
curl "https://public-artifacts.taskcluster.net/$TASK_ID/0/public/build/target.tar.bz2" | tar -xvja

# Download build information of Firefox
CHANGESET=$(wget -q -O - "https://public-artifacts.taskcluster.net/$TASK_ID/0/public/build/target.json" | python -c "import sys,json; print(json.load(sys.stdin)['moz_source_stamp'])")

# Checkout Framboise
retry git clone -v --depth 1 https://github.com/mozillasecurity/framboise.git
rm -rf framboise/modules

# Checkout private Framboise modules
retry git clone -v --depth 1 git@framboise-modules:mozillasecurity/framboise-modules framboise/modules

# Install Framboise dependencies
pip3 -q install -r framboise/requirements.txt

# Checkout fuzzing resources
git clone https://github.com/mozillasecurity/fuzzdata

# Checkout and setup FuzzManager
retry git clone -v --depth 1 https://github.com/mozillasecurity/FuzzManager.git fuzzmanager
pip -q install -r fuzzmanager/requirements.txt

# Create base FuzzManager configuration
cat > /home/ubuntu/.fuzzmanagerconf << EOL
[Main]
serverhost = fuzzmanager.fuzzing.mozilla.org
serverport = 443
serverproto = https
serverauthtoken = 798e42d7527d35c54418cfe8f3a3987142ac7e83
sigdir = /home/ubuntu/signatures
EOL
echo "clientid =" `curl --retry 5 -s http://169.254.169.254/latest/meta-data/public-hostname` >> /home/ubuntu/.fuzzmanagerconf

# Create binary FuzzManager configuration
cat > /home/ubuntu/firefox/firefox.fuzzmanagerconf << EOL
[Main]
platform = x86-64
product = ${ARTIFACT_NAME}
product_version = ${CHANGESET}
os = `uname -s`
EOL

# Ensure proper permissions
chown -R ubuntu:ubuntu /home/ubuntu

# Run Framboise as user "ubuntu"
su -c "screen -t framboise -dmS framboise xvfb-run python3 ./framboise.py -fuzzer 1:WebGL,1:WebGL2 -with-events -with-set-interval" ubuntu

