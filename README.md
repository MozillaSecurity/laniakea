Laniakea
========


[![Build Status](https://api.travis-ci.org/MozillaSecurity/laniakea.svg)](https://api.travis-ci.org/MozillaSecurity/laniakea.svg)


<h3>Setup</h3>
```
pip install -r requirements.txt
```

Add your AWS credentials to a custom profile inside your ~/.boto configuration file.
```
[profile laniakea]
aws_access_key_id = <your_access_key_id>
aws_secret_access_key = <your_secret_key>
```

Complement the provided **images.json** file with your AWS AMI information.
```
# Example: an on-demand instance
"default": {
  "image_id":"ami-<AMI_ID>",
  "instance_type": "<INSTANCE_TYPE>",
  "security_groups": ["laniakea"],
  "key_name": "<AWS_KEY_NAME>",
  "min_count": 3,
  "max_count": 3
}

# Example: a spot instance
"peach": {
  "image_id":"ami-<AMI_ID>",
  "instance_type": "<INSTANCE_TYPE>",
  "security_groups": ["laniakea"],
  "key_name": "<AWS_KEY_NAME>",
  "count": 3
}
```

Add your UserData script - which is going to be used for provisioning your EC2 instances - to the "userdata/" folder.

**NOTE**
In the likely case that you want to use a custom UserData script rather than modifying the "default.sh" file, then you need to point the "-userdata" parameter to that file.

Please refer to https://help.ubuntu.com/community/CloudInit to learn more about UserData scripts.


<h3>Basic Usage Examples</h3>

Run N on-demand instances with a custom -userdata script
```
% ./laniakea.py -create-on-demand -tags Name=peach -userdata userdata/peach.private.sh
```

Run N spot instances with a custom -userdata script and a -max-spot-price of $0.05
```
% ./laniakea.py -create-spot -tags Name=peach -image-name peach -userdata userdata/peach.private.sh -image-args count=10
```

Show which instances are running and are tagged with the name 'peach'
```
% ./laniakea.py -status -only tag:Name=peach instance-state-code=16
```

**Hint** Filters support wildcards. Example: "tag:Name=peach-*" would be suitable to list all instances having the  word "peach" as prefix of a tag name. For a list of available filters refer to http://docs.aws.amazon.com/AWSEC2/latest/CommandLineReference/ApiReference-cmd-DescribeInstances.html

Terminate all running instances which are tagged with the name 'peach'
```
% ./laniakea.py -terminate -only tag:Name=peach
```

Scale down and terminate the oldest N running instances
```
% ./laniakea.py -terminate N -only tag:Name=peach
```

Terminate a specific instance by id
```
% ./laniakea.py -status -only tag:Name=peach instance-id=i-9110fa9e
```

<h3>UserData Reference</h3>

Laniakea supports various macros to construct and maintain user-data files.
```
@import(path_to_other_userdata_file)@
@macro_name@
```
You can use the "-list-userdata-macros" option to print out available macros inside a user-data file. Each of these macros can then be substituted with the -userdata-macros option.


<h3>Help Menu</h3>
```
usage: ./laniakea.py
     (-create-on-demand | -create-spot | -stop [n] | -terminate [n] | -status)
     [-userdata path] [-list-userdata-macros]
     [-userdata-macros k=v [k=v ...]] [-tags k=v [k=v ...]]
     [-only k=v [k=v ...]] [-images path] [-image-name str]
     [-image-args k=v [k=v ...]] [-profile str]
     [-max-spot-price #] [-verbosity {1,2,3,4,5}]

Laniakea Runtime

Mandatory Arguments:
  -create-on-demand     Create on-demand instances (default: False)
  -create-spot          Create spot instances (default: False)
  -stop [n]             Stop active instances (default: None)
  -terminate [n]        Terminate active instances (default: None)
  -status               List current state of instances (default: False)

UserData Arguments:
  -userdata path        UserData script for cloud-init (default:
                        userdata/default.sh)
  -list-userdata-macros
                        List available macros (default: False)
  -userdata-macros k=v [k=v ...]
                        Custom macros (default: None)

Optional Arguments:
  -tags k=v [k=v ...]   Assign tags to instances (default: None)
  -only k=v [k=v ...]   Filter instances (default: None)
  -images path          EC2 image definitions (default: images.json)
  -image-name str       Name of image definition (default: default)
  -image-args k=v [k=v ...]
                        Custom image arguments (default: None)
  -profile str          AWS profile name in .boto (default: laniakea)
  -max-spot-price #     Max price for spot instances (default: 0.05)
  -region str           EC2 region (default: us-west-2)
  -verbosity {1,2,3,4,5}
                        Log level for the logging module (default: 2)

The exit status is 0 for non-failures and 1 for failures.
```
