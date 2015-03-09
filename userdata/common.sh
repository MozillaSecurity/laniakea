# https://help.ubuntu.com/community/CloudInit
# http://www.knowceantech.com/2014/03/amazon-cloud-bootstrap-with-userdata-cloudinit-github-puppet/

# Bash Utilities
function retry {
	for i in {1..5}; do $@ && break || sleep 1; done
}

