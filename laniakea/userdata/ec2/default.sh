#!/bin/bash -ex

@import(common.sh)@

apt-get --yes --quiet update
apt-get --yes --quiet install build-essential python3 python3-pip python-dev git

export HOME=/home/ubuntu
cd $HOME

ssh-keyscan github.com >> $HOME/.ssh/known_hosts

pip3 install fuzzfetch
fuzzfetch -a -o $HOME -n firefox

chown -R ubuntu:ubuntu $HOME
