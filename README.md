<p align="center">
  <img src="https://github.com/posidron/posidron.github.io/raw/master/static/images/laniakea.png" alt="Logo" />
</p>

<p align="center">
Laniakea is a utility for managing instances at various cloud providers and aids in setting up a fuzzing cluster.
</p>

<p align="center">
<a href="https://travis-ci.org/MozillaSecurity/laniakea"><img src="https://api.travis-ci.org/MozillaSecurity/laniakea.svg?branch=master" alt="Build Status"></a>
<a href="https://www.irccloud.com/invite?channel=%23fuzzing&amp;hostname=irc.mozilla.org&amp;port=6697&amp;ssl=1"><img src="https://img.shields.io/badge/IRC-%23fuzzing-1e72ff.svg?style=flat" alt="IRC"></a>
</p>


<h2>Table of Contents</h2>

* [Setup](#Setup)
* [Laniakea Help Menu](#LaniakeaHelpMenu)
* [Packet Bare Metal](#PacketBareMetal)
  * [Basic Usage Example](#BasicPacketUsageExamples)
  * [Packet Help Menu](#PacketHelpMenu)
* [Amazon EC2](#AmazonEC2)
  * [Basic Usage Examples](#BasicUsageExamples)
  * [EC2 Help Menu](#EC2HelpMenu)
* [Azure](#Azure)
  * [Basic Usage Examples](#BasicAzureUsageExamples)
  * [Azure Help Menu](#AzureHelpMenu)
* [UserData Reference](#UserDataReference)
* [Extending Laniakea](#ExtendingLaniakea)


<a name="Setup"><h2>Setup</h2></a>

```bash
pip install laniakea
```

or

```bash
python3 -m pip install -r requirements.txt
python3 -m laniakea -h
```

<a name="LaniakeaHelpMenu"><h2>Laniakea Help Menu</h2></a>

```
usage: laniakea [-verbosity {1,2,3,4,5}] [-settings path] [-userdata path] [-list-userdata-macros] [-print-userdata]
                [-userdata-macros k=v [k=v ...]]
                ...

Laniakea Runtime v0.9

Laniakea Cloud Providers:
  Use -h to see the help menu of each provider.


    azure                         Microsoft Azure
    packet                        Packet Bare Metal
    ec2                           Amazon Elastic Cloud Computing

Laniakea Base Parameters:
  -verbosity {1,2,3,4,5}          Log sensitivity. (default: 2)
  -settings path                  Laniakea core settings. (default: /Users/posidron/Library/Application
                                  Support/laniakea/laniakea.json)

UserData Parameters:
  -userdata path                  UserData script for the provisioning process. (default: None)
  -list-userdata-macros           List available macros. (default: False)
  -print-userdata                 Print the UserData script to stdout. (default: False)
  -userdata-macros k=v [k=v ...]  Custom macros for the UserData. (default: None)

The exit status is 0 for non-failures and 1 for failures.
```

<a name="PacketBareMetal"><h2>Packet Bare Metal</h2></a>

Add your Packet auth token and a project name with the associated project id to the `packet.json` configuration file.

```json
cat laniakea/examples/packet.json
{
    "auth_token": "YOUR_AUTH_TOKEN",
    "projects": {
        "fuzzing": "YOUR_PROJECT_ID"
    }
}
```
<a name="BasicPacketUsageExamples"><h3>Basic Usage Examples</h3></a>

Creating either on-demand (`-create-demand`) or spot (`-create-spot`) devices:
```bash
laniakea packet -project fuzzing -create-demand -tags fuzzers -count 3
```

Show created devices by applying a tag based filter:
```bash
laniakea packet -project fuzzing -list-devices -only tags=fuzzers
```

Terminate all devices, matching the filter criteria:
```bash
laniakea packet -project fuzzing -terminate -only tags=fuzzers
```


<a name="PacketHelpMenu"><h3>Packet Help Menu</h3></a>

```
usage: laniakea packet [-h] [-create-demand | -create-spot | -reboot [n] | -stop [n] | -terminate [n]]
                       [-create-volume s [s ...]] [-conf path] [-list-projects] [-list-plans] [-list-operating-systems]
                       [-list-spot-prices] [-list-facilities] [-list-devices] [-project project] [-tags seq [seq ...]]
                       [-region region] [-os name] [-plan name] [-max-spot-price #] [-count #] [-only k=v [k=v ...]]

optional arguments:
  -h, --help                show this help message and exit

Mandatory Packet Parameters:
  -create-demand            Create an on demand based bare metal device instance. (default: False)
  -create-spot              Create a spot price based bare metal device instance. (default: False)
  -reboot [n]               Reboot active instances. (default: None)
  -stop [n]                 Stop active instances. (default: None)
  -terminate [n]            Terminate active instances. (default: None)

Optional Parameters:
  -create-volume s [s ...]  Create storage: <plan> <size> <region> <description> (default: None)
  -conf path                Packet configuration (default: /Users/posidron/Library/Application
                            Support/laniakea/examples/packet/packet.json)
  -list-projects            List available projects. (default: False)
  -list-plans               List available plans. (default: False)
  -list-operating-systems   List available operating systems. (default: False)
  -list-spot-prices         List spot prices. (default: False)
  -list-facilities          List available facilities. (default: False)
  -list-devices             List devices under given project name. (default: False)
  -project project          The project to perform operations on. (default: fuzzing)
  -tags seq [seq ...]       Tags associated with the instance. (default: None)
  -region region            The facility in which the instance is going to run. (default: nrt1)
  -os name                  The operating system for the created instance. (default: ubuntu_18_04)
  -plan name                The instance type to run. (default: baremetal_0)
  -max-spot-price #         Max price for spot instances. (default: 0.05)
  -count #                  The amount of devices to be spawned. (default: 1)
  -only k=v [k=v ...]       Filter instances by criterias. (default: None)
```

<a name="AmazonEC2"><h2>Amazon EC2</h2></a>

Add your AWS credentials to a custom profile inside your `~/.boto` configuration file.
```ini
[profile laniakea]
aws_access_key_id = <your_access_key_id>
aws_secret_access_key = <your_secret_key>
```

Complement the provided `amazon.json` file with your AWS AMI information (see `laniakea -h` for location).
```json
# Example: an on-demand instance
"default": {
  "image_id":"ami-<AMI_ID>",
  "instance_type": "<INSTANCE_TYPE>",
  "security_groups": ["laniakea"],
  "key_name": "<AWS_KEY_NAME>",
  "instance_profile_name": "<name-of-role>",
  "min_count": 3,
  "max_count": 3
}

# Example: a spot instance
"peach": {
  "image_id":"ami-<AMI_ID>",
  "instance_type": "<INSTANCE_TYPE>",
  "security_groups": ["laniakea"],
  "key_name": "<AWS_KEY_NAME>",
  "instance_profile_name": "<name-of-role>",
  "count": 3
}
```

Add your UserData script - which is going to be used for provisioning your EC2 instances - to the `userdata/` folder.


> In the likely case that you want to use a custom UserData script rather than modifying the `default.sh` file, then you need to point the `-userdata` parameter to that file.

Please refer to https://help.ubuntu.com/community/CloudInit to learn more about UserData scripts.


<a name="BasicUsageExamples"><h3>Basic Usage Examples</h3></a>

Run N on-demand instances with a custom -userdata script
```bash
laniakea ec2 -create-on-demand -tags Name=peach -userdata userdata/peach.private.sh
```

Run N spot instances with a custom -userdata script and a -max-spot-price of $0.05
```bash
laniakea ec2 -create-spot -tags Name=peach -image-name peach -userdata userdata/peach.private.sh -image-args count=10
```

Show which instances are running and are tagged with the name 'peach'
```bash
laniakea ec2 -status -only tag:Name=peach instance-state-code=16
```

> Filters support wildcards. Example: "tag:Name=peach-*" would be suitable to list all instances having the  word "peach" as prefix of a tag name. For a list of available filters refer to http://docs.aws.amazon.com/AWSEC2/latest/CommandLineReference/ApiReference-cmd-DescribeInstances.html

Terminate all running instances which are tagged with the name 'peach'
```bash
laniakea ec2 -terminate -only tag:Name=peach
```

Scale down and terminate the oldest N running instances
```bash
laniakea ec2 -terminate N -only tag:Name=peach
```

Terminate a specific instance by id
```bash
laniakea ec2 -status -only tag:Name=peach instance-id=i-9110fa9e
```

List available macros in a UserData script
```bash
laniakea ec2 -list-userdata-macros -userdata userdata/peach.pit.sh
```

<a name="EC2HelpMenu"><h3>EC2 Help Menu</h3></a>

```bash
python3 -m laniakea ec2 -h
```

```
usage: laniakea ec2 [-h] [-create-on-demand | -create-spot | -stop [n] | -terminate [n] | -status | -run cmd |
                    -list-userdata-macros | -print-userdata] [-userdata path] [-userdata-macros k=v [k=v ...]]
                    [-tags k=v [k=v ...]] [-only k=v [k=v ...]] [-images path] [-image-name str]
                    [-image-args k=v [k=v ...]] [-profile str] [-max-spot-price #] [-region REGION] [-zone ZONE]
                    [-root-device-type {ebs,instance_store}] [-ebs-size EBS_SIZE] [-ebs-volume-type {gp2,io1,standard}]
                    [-ebs-volume-delete-on-termination]

optional arguments:
  -h, --help                            show this help message and exit

Mandatory EC2 Parameters:
  -create-on-demand                     Create on-demand instances. (default: False)
  -create-spot                          Create spot instances. (default: False)
  -stop [n]                             Stop active instances. (default: None)
  -terminate [n]                        Terminate active instances. (default: None)
  -status                               List current state of instances. (default: False)
  -run cmd                              Execute commands via SSH (default: )
  -list-userdata-macros                 List available macros. (default: False)
  -print-userdata                       Print the UserData script to stdout. (default: False)

UserData Parameters:
  -userdata path                        UserData script for cloud-init process. (default:
                                        /Users/posidron/Library/Application Support/laniakea/userdata/ec2/default.sh)
  -userdata-macros k=v [k=v ...]        Custom macros for the UserData. (default: None)

Optional Parameters:
  -tags k=v [k=v ...]                   Assign tags to instances. (default: None)
  -only k=v [k=v ...]                   Filter instances by criterias. (default: None)
  -images path                          EC2 image definitions. (default: /Users/posidron/Library/Application
                                        Support/laniakea/amazon.json)
  -image-name str                       Name of image definition. (default: default)
  -image-args k=v [k=v ...]             Custom image arguments. (default: None)
  -profile str                          AWS profile name in the .boto configuration. (default: laniakea)
  -max-spot-price #                     Max price for spot instances. (default: 0.05)
  -region REGION                        EC2 region name. (default: us-west-2)
  -zone ZONE                            EC2 placement zone. (default: None)
  -root-device-type {ebs,instance_store}
                                        The root device type. (default: ebs)
  -ebs-size EBS_SIZE                    The root disk space size. (default: None)
  -ebs-volume-type {gp2,io1,standard}   The root disk volume type. (default: gp2)
  -ebs-volume-delete-on-termination     Delete the root EBS volume on termination. (default: False)
```

<a name="UserDataReference"><h2>UserData Reference</h2></a>

Laniakea supports various macros to construct and maintain user-data files.
```
@import(path_to_other_userdata_file)@
@macro_name@
```
You can use the `-list-userdata-macros` option to print out available macros inside a user-data file. Each of these macros can then be substituted with the `-userdata-macros` option.

<a name="Azure"><h2>Azure</h2></a>

Laniakea supports supports Azure by creating Virtual Machine instances using Azure Resource Management (ARM) Templates. These are JSON files that describe how a Virtual Machine should be
set up and deployed. This includes parameters such as: machine size, OS parameters, configuration scripts, etc. An example template can be found in the laniaka/examples/azure/template.json. An example
configuration script can be found at http://www.github.com/rforbes/azure-configs/deploy-domino.ps1

When we create resources in Azure we start by creating a Resource Group. Azure uses the Resource Group to store all the resources that are created. This includes, the Virtual machine, any storage for the VM, network interfaces, and IP addresses. We use the -fuzzer flag to set the name of the Resource Group. The name cannot be longer than 12 characters. In order to delete a pool, we delete the Resource Group.

We keep keys and other secrets in AWS using credstash.

Add your AWS credentials to a custom profile inside your `~/.boto` configuration file.
```ini
[profile laniakea]
aws_access_key_id = <your_access_key_id>
aws_secret_access_key = <your_secret_key>
```

Create a azure.json file. This file contains the secrets required for accessing and launching in Azure, the username and password of the VMs being created, and the AWS credentials for accessing
credstash. Below is example:

Complement the provided `amazon.json` file with your AWS AMI information (see `laniakea -h` for location).
```json
{
    "keys": {
        "subscription_id":  "",
        "client_id": "",
        "client_secret": "",
        "tenant_id": ""
    },
    "credentials": {
        "username": "",
        "password": ""
    },
    "aws-credentials": {
        "aws_key_id":"",
        "aws_secret":""
    }
}
```
The subscription ID, client ID, client secret, and tenant ID are all found in the Azure portal.

Virtual Machine configuration happens using a powershell script that is called in the ARM template.

THe following section of the ARM template is where the script is set.

```json
"properties": {
    "publisher": "Microsoft.Compute",
    "type": "CustomScriptExtension",
    "typeHandlerVersion": "1.9",
    "autoUpgradeMinorVersion": true,
    "settings": {
        "fileUris": [
            "https://raw.githubusercontent.com/rforbes/azure-configs/master/deploy-domino.ps1"
        ]
    },
```
<a name="BasicAzureUsageExamples"><h3>Basic Usage Examples</h3></a>

Run 3 instances
```bash
laniakea azure -create -fuzzer domino -region eastus count 3
```
Terminate all running instances
```bash
laniakea azure -terminate -group-name domino
```
<a name="AzureHelpMenu"><h3>Azure Help Menu</h3></a>

```bash
python3 -m laniakea azure -h
```

```
usage: laniakea azure [-h] [-region name] [-count n] [-create] [-delete] [-group-name name]
                      [-azure path] [-template path]

optional arguments:
  -h, --help        show this help message and exit

Mandatory Azure Parameters:
  -region name      Azure region. (default: None)
  -count n          Number of instances to launch. (default: 1)
  -create           Create an instance pool. (default: False)
  -delete           Delete an instance pool. (default: False)
  -group-name name  Group name to be deleted. (default: None)
  -azure path       Deployment template for Windows Azure (default:
                    C:\Users\rforbes\AppData\Local\Mozilla Security\laniakea\azure.json)

UserData Parameters:
  -template path    Deployment template for Windows Azure (default:
                    C:\Users\rforbes\AppData\Local\Mozilla
                    Security\laniakea\userdata\azure\template.json)
```
<a name="ExtendingLaniakea"><h2>Extending Laniakea</h2></a>

To extend Laniakea with new cloud providers you need to ...

* Add a new folder in `laniakea/core/providers/<cloud_provider>`
* Write a command-line interface and put it into the `__init__.py`
* Write an API manager class and name it `manager.py`
* Add additional files (i.e userdata scripts) to `laniakea/userdata/`
* Add additional configuration files to `laniakea/examples/`
