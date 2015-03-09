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

Add your user-data script - which is going to be used for provisioning your EC2 instances - to "userdata/".
If you add a custom user-script rather than modifying "default.sh" then provide the path to that script to the "-userdata" parameter.

<h4>Basic Usage</h4>
```
% ./laniakea.py -create-spot -tags Name=peach -image-name ec2-spot -userdata userdata/peach.private.sh
% ./laniakea.py -create-on-demand -tags Name=peach -userdata userdata/peach.private.sh
% ./laniakea.py -status -only tag:Name=peach instance-state-code=16
% ./laniakea.py -terminate -only tag:Name=peach
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
