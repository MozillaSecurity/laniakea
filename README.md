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

Add your setup script which is going to be used for provisioning your EC2 instances to user_data/. If you add a custom script rather than modifying "default.sh" than add the path to the parameter "-user-data".

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

