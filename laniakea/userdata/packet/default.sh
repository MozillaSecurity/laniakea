#!/bin/bash -ex

# Essentials
apt-get --yes --quiet update
apt-get --yes --quiet install python python-pip python-dev git puppet-common build-essential

pip install fuzzfetch