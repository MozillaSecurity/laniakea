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

# Peach
#sudo apt-get --yes --quiet install \
#	libxml2-dev libxslt1-dev lib32z1-dev xterm
#sudo pip install \
#	Twisted==14.0.0 lxml==3.3.5 psutil==2.1.1 pyasn1==0.1.7 tlslite==0.4.6 

# FuzzManager
#sudo pip install \
#	Django==1.7.1 numpy==1.9.1 djangorestframework==2.4.4 requests>=2.5.0 lockfile>=0.8
