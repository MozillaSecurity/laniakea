#!/bin/bash -ex

@import(userdata/common.sh)@

# Essential Packages

# The following packages are part of the FuzzingOS base image:
#sudo apt-get --yes --quiet update
#sudo apt-get --yes --quiet upgrade
#sudo apt-get --yes --quiet build-dep firefox
#sudo apt-get --yes --quiet install \
#	python python-pip python-dev git mercurial s3cmd

# Peach
#sudo apt-get --yes --quiet install \
#	libxml2-dev libxslt1-dev lib32z1-dev xterm
#sudo pip install \
#	Twisted==14.0.0 lxml==3.3.5 psutil==2.1.1 pyasn1==0.1.7 tlslite==0.4.6 

# FuzzManager
#sudo pip install \
#	Django==1.7.1 numpy==1.9.1 djangorestframework==2.4.4 requests>=2.5.0 lockfile>=0.8

# -----------------------------------------------------------------------------

# Add GitHub as a known host
ssh-keyscan github.com >> /root/.ssh/known_hosts

# Add this key as deploy key to the GitHub project
# Command: ssh-keygen -t rsa -C "Deploy key for Peach"
cat << EOF > /root/.ssh/id_rsa.peach
-----BEGIN RSA PRIVATE KEY-----
-----END RSA PRIVATE KEY-----
EOF

# Add this key as deploy key to the GitHub project
# Command: ssh-keygen -t rsa -C "Deploy key for Pits"
cat << EOF > /root/.ssh/id_rsa.pits
-----BEGIN RSA PRIVATE KEY-----
-----END RSA PRIVATE KEY-----
EOF

# Setup Key Indentities
cat << EOF > /root/.ssh/config
Host *
	StrictHostKeyChecking no

Host peach github.com
Hostname github.com
IdentityFile /root/.ssh/id_rsa.peach

Host pits github.com
Hostname github.com
IdentityFile /root/.ssh/id_rsa.pits
EOF

# Set Key Permissions
chmod 600 /root/.ssh/id_rsa.*


# -----------------------------------------------------------------------------

cd /home/ubuntu

# Target desscription for Firefox
TARGET_PRODUCT="mozilla-inbound-linux64-asan"
TARGET_LOCATION="ftp.mozilla.org/pub/mozilla.org/firefox/tinderbox-builds/${TARGET_PRODUCT}/latest"
TARGET_URL="ftp://${TARGET_LOCATION}"
retry wget --force-directories --no-parent --glob=on ${TARGET_URL}/firefox-*.en-US.linux-x86_64-asan.tar.bz2
retry wget --force-directories --no-parent --glob=on ${TARGET_URL}/*.txt -O ${TARGET_LOCATION}/revision.txt
tar xvfj ${TARGET_LOCATION}/firefox-*.en-US.linux-x86_64-asan.tar.bz2
TARGET_VERSION=`cat ${TARGET_LOCATION}/revision.txt`

# Checkout Peach
retry git clone -v --depth 1 git@peach:MozillaSecurity/peach.git
cd peach
retry git clone -v --depth 1 git@pits:MozillaSecurity/pits.git Pits
pip -q install -r requirements.txt
retry python scripts/userdata.py -sync

# Checkout and setup FuzzManager
retry git clone -v --depth 1 https://github.com/MozillaSecurity/FuzzManager.git Peach/Utilities/FuzzManager
pip install -r Peach/Utilities/FuzzManager/requirements.txt

# Create base FuzzManager configuration
cat > /home/ubuntu/.fuzzmanagerconf << EOL
[Main]
serverhost = darpa.spdns.de
serverport = 8000
serverproto = http
serverauthtoken = @AUTH_TOKEN@
sigdir = /home/ubuntu/signatures
EOL
echo "clientid =" `curl --retry 5 -s http://169.254.169.254/latest/meta-data/public-hostname` >> /home/ubuntu/.fuzzmanagerconf

# Create binary FuzzManager configuration
cat > /home/ubuntu/firefox/firefox.fuzzmanagerconf << EOL
[Main]
platform = x86-64
product = ${TARGET_PRODUCT}
product_version = ${TARGET_VERSION}
os = `uname -s`
EOL

# Ensure proper permissions
chown -R ubuntu:ubuntu /home/ubuntu

# Run FuzzingBot as user "ubuntu"
#su -c "xvfb-run ./scripts/peachbot.py -tasks 50 -testcases 50000 -data . -pits Pits/" ubuntu
su -c "screen -t peach -dmS peach xvfb-run ./scripts/peachbot.py -tasks 50 -testcases 50000 -data . -pits Pits/" ubuntu
