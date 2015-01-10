Laniakea
========


![](http://people.mozilla.com/~cdiehl/img/galaxy.jpg)


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

Add your user-data script - which is going to be used for provisioning your EC2 instances - to "userdata/".
If you add a custom user-script rather than modifying "default.sh" then provide the path to that script to the "-userdata" parameter.

<h4>Basic Usage</h4>
```
% ./laniakea.py -create-on-demand -tags Name=peach
% ./laniakea.py -create-spot -tags Name=peach -image-name ec2-spot -userdata userdata/peach.private.sh
% ./laniakea.py -status -only tag:Name=peach
% ./laniakea.py -terminate -only tag:Name=peach
```

<h4>Example</h4>
```
% ./laniakea.py -create-on-demand -tags Name=peach -userdata userdata/peach.private.sh
[Laniakea] 2015-01-05 00:17:15 INFO: Using image definition "default" from images.json.
[Laniakea] 2015-01-05 00:17:15 INFO: Adding user data script content from userdata/peach.private.sh.
[Laniakea] 2015-01-05 00:17:15 INFO: Using Boto configuration profile "laniakea".
[Laniakea] 2015-01-05 00:17:40 INFO: i-7332e57d is running at ec2-54-149-44-1.us-west-2.compute.amazonaws.com (54.149.44.1)
[Laniakea] 2015-01-05 00:17:40 INFO: i-7132e57f is running at ec2-54-149-43-14.us-west-2.compute.amazonaws.com (54.149.43.14)
[Laniakea] 2015-01-05 00:17:40 INFO: i-7c32e572 is running at ec2-54-149-113-86.us-west-2.compute.amazonaws.com (54.149.113.86)
[Laniakea] 2015-01-05 00:17:41 INFO: i-7432e57a is running at ec2-54-149-10-175.us-west-2.compute.amazonaws.com (54.149.10.175)
[Laniakea] 2015-01-05 00:17:41 INFO: i-7232e57c is running at ec2-54-149-43-154.us-west-2.compute.amazonaws.com (54.149.43.154)
[Laniakea] 2015-01-05 00:17:41 INFO: i-7d32e573 is running at ec2-54-149-77-74.us-west-2.compute.amazonaws.com (54.149.77.74)
[Laniakea] 2015-01-05 00:17:41 INFO: i-7732e579 is running at ec2-54-68-133-104.us-west-2.compute.amazonaws.com (54.68.133.104)
[Laniakea] 2015-01-05 00:17:41 INFO: i-7632e578 is running at ec2-54-149-111-110.us-west-2.compute.amazonaws.com (54.149.111.110)
[Laniakea] 2015-01-05 00:17:41 INFO: i-7032e57e is running at ec2-54-149-93-26.us-west-2.compute.amazonaws.com (54.149.93.26)
[Laniakea] 2015-01-05 00:17:41 INFO: i-7532e57b is running at ec2-54-149-38-127.us-west-2.compute.amazonaws.com (54.149.38.127)

% ./laniakea.py -status -only tag:Name=peach instance-state-code=16
[Laniakea] 2015-01-05 00:34:57 INFO: Using image definition "default" from images.json.
[Laniakea] 2015-01-05 00:34:57 INFO: Adding user data script content from userdata/default.sh.
[Laniakea] 2015-01-05 00:34:57 INFO: Using Boto configuration profile "laniakea".
[Laniakea] 2015-01-05 00:35:01 INFO: i-e536e1eb is running at 54.149.155.103 - tags: {u'Name': u'peach'}
[Laniakea] 2015-01-05 00:35:01 INFO: i-bd35e2b3 is running at 54.149.216.72 - tags: {u'Name': u'peach'}
[Laniakea] 2015-01-05 00:35:01 INFO: i-ee36e1e0 is running at 54.149.226.196 - tags: {u'Name': u'peach'}
[Laniakea] 2015-01-05 00:35:01 INFO: i-0534e30b is running at 54.149.106.23 - tags: {u'Name': u'peach'}
[Laniakea] 2015-01-05 00:35:01 INFO: i-2735e229 is running at 54.149.112.81 - tags: {u'Name': u'peach'}
[Laniakea] 2015-01-05 00:35:01 INFO: i-aa35e2a4 is running at 54.149.121.174 - tags: {u'Name': u'peach'}
[Laniakea] 2015-01-05 00:35:01 INFO: i-2a35e224 is running at 54.149.95.195 - tags: {u'Name': u'peach'}
[Laniakea] 2015-01-05 00:35:01 INFO: i-a534e3ab is running at 54.149.212.119 - tags: {u'Name': u'peach'}
[Laniakea] 2015-01-05 00:35:01 INFO: i-9e33e490 is running at 54.68.1.19 - tags: {u'Name': u'peach'}
[Laniakea] 2015-01-05 00:35:01 INFO: i-5336e15d is running at 54.68.17.140 - tags: {u'Name': u'peach'}
```

<h4>Help Menu</h4>
```
usage: ./laniakea.py
                     (-create-on-demand | -create-spot | -stop | -terminate | -status)
                     [-userdata path] [-list-userdata-macros]
                     [-userdata-macros k=v [k=v ...]] [-tags k=v [k=v ...]]
                     [-only k=v [k=v ...]] [-image-name str] [-images path]
                     [-profile str] [-max-spot-price #]
                     [-verbosity {1,2,3,4,5}]

Laniakea Runtime

Mandatory Arguments:
  -create-on-demand     Create on-demand instances (default: False)
  -create-spot          Create spot instances (default: False)
  -stop                 Stop active instances (default: False)
  -terminate            Terminate active instances (default: False)
  -status               List current state of instances (default: False)

UserData Arguments:
  -userdata path        UserData script for cloud-init (default:
                        userdata/default.sh)
  -list-userdata-macros
                        List available macros (default: False)
  -userdata-macros k=v [k=v ...]
                        Set custom macros (default: None)

Optional Arguments:
  -tags k=v [k=v ...]   Assign tags to instances (default: None)
  -only k=v [k=v ...]   Filter instances (default: None)
  -image-name str       Name of image definition (default: default)
  -images path          EC2 image definitions (default: images.json)
  -profile str          AWS profile name in .boto (default: laniakea)
  -max-spot-price #     Max price for spot instances (default: 0.05)
  -verbosity {1,2,3,4,5}
                        Log level for the logging module (default: 2)

The exit status is 0 for non-failures and 1 for failures.
```
