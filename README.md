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

Edit images.json with your AWS AMI data
```
"default": {
    "image_id":"ami-<AMI_ID>",
	"instance_type": "<INSTANCE_TYPE",
	"security_groups": ["laniakea"],
	"key_name": "<AWS_KEY_NAME>"
}
```

Add your setup script which is going to be used for provisioning your EC2 instances to "user_data/". 
If you add a custom script rather than modifying "default.sh" then use the "-user-data" parameter.

<h4>Basic Usage</h4>
```
% ./laniakea.py -create -tags '{"Name": "peach"}'
% ./laniakea.py -terminate -only "{'tag:Name': 'peach'}"
% ./laniakea.py -status -only "{'tag:Name': 'peach'}"
```

<h4>Example</h4>
```
% ./laniakea.py -status -only "{'tag:Name': 'peach'}"
[Laniakea] 2014-11-29 12:00:22,415 INFO: Using image definition 'default' from images.json
[Laniakea] 2014-11-29 12:00:22,415 INFO: Adding user data script content from user_data/default.sh
[Laniakea] 2014-11-29 12:00:22,415 INFO: Using Boto configuration profile 'laniakea'
% ./laniakea.py -create -tags '{"Name": "peach"}' -count 3
[...]
[Laniakea] 2014-11-29 12:01:24,879 INFO: DNS: ec2-54-149-42-195.us-west-2.compute.amazonaws.com (54.149.42.195)
[Laniakea] 2014-11-29 12:01:43,414 INFO: DNS: ec2-54-149-30-28.us-west-2.compute.amazonaws.com (54.149.30.28)
[Laniakea] 2014-11-29 12:01:59,017 INFO: DNS: ec2-54-149-44-253.us-west-2.compute.amazonaws.com (54.149.44.253)
% ./laniakea.py -terminate -only "{'tag:Name': 'peach'}"
[...]
% ./laniakea.py -status -only "{'tag:Name': 'peach'}"
[...]
[Laniakea] 2014-11-29 12:03:20,083 INFO: [(u'i-e28797ed', u'terminated')] - {u'Name': u'peach'}
[Laniakea] 2014-11-29 12:03:20,394 INFO: [(u'i-ab372ba4', u'terminated')] - {u'Name': u'peach'}
[Laniakea] 2014-11-29 12:03:20,702 INFO: [(u'i-98312d97', u'terminated')] - {u'Name': u'peach'}
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
