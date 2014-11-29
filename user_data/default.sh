#!/bin/sh
set -e -x

# Essentials
apt-get --yes --quiet update
apt-get --yes --quiet install python python-pip python-dev git puppet-common build-essential

# Fetch puppet configuration
mv /etc/puppet /etc/puppet.orig
git clone https://bitbucket.org/rimey/hello-ec2-puppetboot.git /etc/puppet

# Run puppet
puppet apply /etc/puppet/manifests/init.pp

# Run fuzzers