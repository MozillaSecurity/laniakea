<p align="center">
  <img src="https://github.com/posidron/posidron.github.io/raw/master/static/images/laniakea.png" alt="Logo" />
</p>

<p align="center">
Laniakea is a utility for managing instances at various cloud providers and aids in setting up a fuzzing cluster it can be used as a tool or as a library.
</p>

<p align="center">
<a href="https://travis-ci.org/MozillaSecurity/laniakea"><img src="https://api.travis-ci.org/MozillaSecurity/laniakea.svg?branch=master" alt="Build Status"></a>
<a href="https://www.irccloud.com/invite?channel=%23fuzzing&amp;hostname=irc.mozilla.org&amp;port=6697&amp;ssl=1"><img src="https://img.shields.io/badge/IRC-%23fuzzing-1e72ff.svg?style=flat" alt="IRC"></a>
</p>

- [Setup](#setup)
- [Supported Modules](#supported-modules)
- [UserData Reference](#userdata-reference)
- [Extending Laniakea](#extending-laniakea)
- [API Documentation](#api-documentation)
- [Laniakea Help Menu](#laniakea-help-menu)

## Setup

```bash
python3 -m pip install laniakea
```

or

```bash
pipenv install laniakea
pipenv run laniakea -h
```

## Supported Modules

- [Google Compute Engine](https://github.com/MozillaSecurity/laniakea/wiki/Google-Compute-Engine)
- [Amazon EC2](https://github.com/MozillaSecurity/laniakea/wiki/Amazon-EC2)
- [Packet Bare Metal](https://github.com/MozillaSecurity/laniakea/wiki/Packet-Bare-Metal)
- [Azure](https://github.com/MozillaSecurity/laniakea/wiki/Microsoft-Azure)

## UserData Reference

Laniakea supports various macros to construct and maintain user-data files.

> Note that not all modules are still supporting UserData files but use a container approach instead i.e Google Compute Engine. You can and probably should spawn containers within UserData files if you plan to chose to use this kind of initialization method.

```
@import(path_to_other_userdata_file)@
@macro_name@
```

You can use the `-list-userdata-macros` option to print out available macros inside a user-data file. Each of these macros can then be substituted with the `-userdata-macros` option.

## Extending Laniakea

To extend Laniakea with new cloud providers you need to ...

- Add a new folder in `laniakea/core/providers/<cloud_provider>`
- Write a command-line interface and put it into the `__init__.py`
- Write an API manager class and name it `manager.py`
- Add additional files (i.e userdata scripts) to `laniakea/userdata/`
- Add additional configuration files to `laniakea/examples/`

## API Documentation

- https://mozillasecurity.github.io/laniakea

## Laniakea Help Menu

```
usage: laniakea [-verbosity {1,2,3,4,5}] [-settings path] [-userdata path] [-list-userdata-macros] [-print-userdata]
                [-userdata-macros k=v [k=v ...]]
                ...

Laniakea Runtime v1.16.0

Laniakea Cloud Providers:
  Use -h to see the help menu of each provider.


    azure                         Microsoft Azure
    ec2                           Amazon Elastic Cloud Computing
    gce                           Google Compute Engine
    packet                        Packet Bare Metal

Laniakea Base Parameters:
  -verbosity {1,2,3,4,5}          Log sensitivity. (default: 2)
  -settings path                  Laniakea core settings. (default: ~/Library/Application Support/laniakea/laniakea.json)

UserData Parameters:
  -userdata path                  UserData script for the provisioning process. (default: None)
  -list-userdata-macros           List available macros. (default: False)
  -print-userdata                 Print the UserData script to stdout. (default: False)
  -userdata-macros k=v [k=v ...]  Custom macros for the UserData. (default: None)

The exit status is 0 for non-failures and 1 for failures.
```
