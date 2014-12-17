#!/bin/sh
# https://help.ubuntu.com/community/CloudInit
# http://www.knowceantech.com/2014/03/amazon-cloud-bootstrap-with-userdata-cloudinit-github-puppet/
set -e -x

# Essential Packages
apt-get --yes --quiet update
apt-get --yes --quiet build-dep firefox 
apt-get --yes --quiet install python python-pip python-dev git
apt-get --yes --quiet install libxml2-dev libxslt1-dev lib32z1-dev # Peach: lxml
apt-get --yes --quiet install s3cmd # Peach: userdata.py
apt-get --yes --quiet install xterm # Peach: agent.py / xterm

# -----------------------------------------------------------------------------

# Add GitHub as a known host
ssh-keyscan github.com >> /root/.ssh/known_hosts

# Add this key as deploy key to the GitHub project
# Command: ssh-keygen -t rsa -C "Deploy key for Peach"
cat << EOF > /root/.ssh/id_rsa.peach.pub
INSERT_PUBLIC_KEY_HERE
EOF

cat << EOF > /root/.ssh/id_rsa.peach
INSERT_PRIVATE_KEY_HERE
EOF

# Add this key as deploy key to the GitHub project
# Command: ssh-keygen -t rsa -C "Deploy key for Pits"
cat << EOF > /root/.ssh/id_rsa.pits.pub
INSERT_PUBLIC_KEY_HERE
EOF

cat << EOF > /root/.ssh/id_rsa.pits
INSERT_PRIVATE_KEY_HERE
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
chmod 600 /root/.ssh/id_rsa.peach
chmod 600 /root/.ssh/id_rsa.pits

# -----------------------------------------------------------------------------


cd /home/ubuntu

# Download Target
wget -r --no-parent -A firefox-*.en-US.linux-x86_64-asan.tar.bz2 https://ftp.mozilla.org/pub/mozilla.org/firefox/tinderbox-builds/mozilla-inbound-linux64-asan/latest/
wget -r --no-parent -A firefox-*.txt https://ftp.mozilla.org/pub/mozilla.org/firefox/tinderbox-builds/mozilla-inbound-linux64-asan/latest/
tar xvfj ftp.mozilla.org/pub/mozilla.org/firefox/tinderbox-builds/mozilla-inbound-linux64-asan/latest/*.tar.bz2

# Checkout Fuzzer
git clone -v --depth 1 git@peach:MozillaSecurity/peach.git
cd peach
git clone -v --depth 1 git@pits:MozillaSecurity/pits.git Pits
pip -q install -r requirements.txt
python scripts/userdata.py -sync

# Run FuzzingBot
xvfb-run ./scripts/peachbot.py -data . -pits Pits/
