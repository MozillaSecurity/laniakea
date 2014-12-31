Laniakea
========

<h4>Setup</h4>
```
Python 2.x or Python 3.x
pip install -r requirements.txt
```

Add your AWS credentials to a custom profile inside your ~/.boto configuration file.
```
[profile laniakea]
aws_access_key_id = <your_access_key_id>
aws_secret_access_key = <your_secret_key>
```

Edit images.json with your AWS AMI data.
```
"default": {
    "image_id":"ami-<AMI_ID>",
	"instance_type": "<INSTANCE_TYPE",
	"security_groups": ["laniakea"],
	"key_name": "<AWS_KEY_NAME>"
}
```

Add your user-data script - which is going to be used for provisioning your EC2 instances - to "user_data/".
If you add a custom user-script rather than modifying "default.sh" then provide the path to that script to the "-user-data" parameter.

<h4>Basic Usage</h4>
```
% ./laniakea.py -create -tags '{"Name": "peach"}'
% ./laniakea.py -status -only "{'tag:Name': 'peach'}"
% ./laniakea.py -terminate -only "{'tag:Name': 'peach'}"
```

<h4>Example</h4>
```
% ./laniakea.py -create -tags '{"Name": "peach"}' -user-data user_data/peach.private.sh -count 10
[Laniakea] 2014-12-31 16:03:29,981 INFO: Using image definition 'default' from images.json
[Laniakea] 2014-12-31 16:03:29,981 INFO: Adding user data script content from user_data/peach.private.sh
[Laniakea] 2014-12-31 16:03:29,983 INFO: Using Boto configuration profile 'laniakea'
[Laniakea] 2014-12-31 16:03:49,456 INFO: DNS: ec2-54-149-71-121.us-west-2.compute.amazonaws.com (54.149.71.121)
[Laniakea] 2014-12-31 16:04:11,155 INFO: DNS: ec2-54-68-178-179.us-west-2.compute.amazonaws.com (54.68.178.179)
[Laniakea] 2014-12-31 16:04:35,418 INFO: DNS: ec2-54-148-68-196.us-west-2.compute.amazonaws.com (54.148.68.196)
[Laniakea] 2014-12-31 16:04:57,099 INFO: DNS: ec2-54-148-107-226.us-west-2.compute.amazonaws.com (54.148.107.226)
[Laniakea] 2014-12-31 16:05:15,949 INFO: DNS: ec2-54-68-97-182.us-west-2.compute.amazonaws.com (54.68.97.182)
[Laniakea] 2014-12-31 16:05:40,318 INFO: DNS: ec2-54-149-134-222.us-west-2.compute.amazonaws.com (54.149.134.222)
[Laniakea] 2014-12-31 16:06:04,742 INFO: DNS: ec2-54-148-226-72.us-west-2.compute.amazonaws.com (54.148.226.72)
[Laniakea] 2014-12-31 16:06:26,297 INFO: DNS: ec2-54-149-147-59.us-west-2.compute.amazonaws.com (54.149.147.59)
[Laniakea] 2014-12-31 16:06:48,115 INFO: DNS: ec2-54-69-42-36.us-west-2.compute.amazonaws.com (54.69.42.36)
[Laniakea] 2014-12-31 16:07:09,967 INFO: DNS: ec2-54-149-255-122.us-west-2.compute.amazonaws.com (54.149.255.122)

% ./laniakea.py -status -only "{'tag:Name': 'peach', 'instance-state-code': 16}"
[Laniakea] 2014-12-31 16:07:35,764 INFO: Using image definition 'default' from images.json
[Laniakea] 2014-12-31 16:07:35,764 INFO: Adding user data script content from user_data/default.sh
[Laniakea] 2014-12-31 16:07:35,764 INFO: Using Boto configuration profile 'laniakea'
[Laniakea] 2014-12-31 16:07:38,169 INFO: [(u'i-d7d11ad9', u'running')] (54.148.68.196) - {u'Name': u'peach'}
[Laniakea] 2014-12-31 16:07:38,523 INFO: [(u'i-c8d11ac6', u'running')] (54.149.71.121) - {u'Name': u'peach'}
[Laniakea] 2014-12-31 16:07:38,857 INFO: [(u'i-59d71c57', u'running')] (54.68.178.179) - {u'Name': u'peach'}
[Laniakea] 2014-12-31 16:07:39,197 INFO: [(u'i-a3d01bad', u'running')] (54.69.42.36) - {u'Name': u'peach'}
[Laniakea] 2014-12-31 16:07:39,533 INFO: [(u'i-d8d11ad6', u'running')] (54.148.107.226) - {u'Name': u'peach'}
[Laniakea] 2014-12-31 16:07:39,883 INFO: [(u'i-02d61d0c', u'running')] (54.149.147.59) - {u'Name': u'peach'}
[Laniakea] 2014-12-31 16:07:40,186 INFO: [(u'i-aed01ba0', u'running')] (54.149.255.122) - {u'Name': u'peach'}
[Laniakea] 2014-12-31 16:07:40,525 INFO: [(u'i-43d61d4d', u'running')] (54.68.97.182) - {u'Name': u'peach'}
[Laniakea] 2014-12-31 16:07:40,859 INFO: [(u'i-1ed61d10', u'running')] (54.148.226.72) - {u'Name': u'peach'}
[Laniakea] 2014-12-31 16:07:41,186 INFO: [(u'i-72d71c7c', u'running')] (54.149.134.222) - {u'Name': u'peach'}
```

<h4>Help Menu</h4>
```
% ./laniakea.py -h
usage: ./laniakea.py (-create | -stop | -terminate | -status) [-tags dict]
                     [-only dict] [-count #] [-image-name str] [-images path]
                     [-profile str] [-user-data path] [-logging #]

Laniakea Runtime

mandatory arguments:
  -create          create instance/s (default: False)
  -stop            stop instance/s (default: False)
  -terminate       terminate instance/s (default: False)
  -status          list current state of instance/s (default: False)

optional arguments:
  -tags dict       tag instance/s (default: {})
  -only dict       filter instance/s (default: {})
  -count #         number of instances to launch (default: 1)
  -image-name str  name of image definition (default: default)
  -images path     EC2 image definitions (default: images.json)
  -profile str     AWS profile name in .boto (default: laniakea)
  -user-data path  data script for cloud-init (default: user_data/default.sh)
  -logging #       verbosity level of the logging module (default: 20)

The exit status is 0 for non-failures and -1 for failures.
```
