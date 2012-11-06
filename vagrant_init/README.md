**NOTE: requires Python 2.7!**

## Initial Setup

Install [Ruby](http://www.ruby-lang.org/en/) and make sure you have
[Bundler](http://gembundler.com/) installed.

## Running Virtual Instances

    # Startup
    vagrant up
    # SSH into machine
    vagrant ssh
    # ...
    # Shutdown
    vagrant halt

## Configuration

Edit or create your own files in the `config` directory. All variables will be
available python scripts under `config` and interpolated in `sh`. For example:

    echo 'GREETING = "Hello"' > config/greeting.py
    cd scripts && python
    >>> from common import *
    >>> print config.GREETING
    Hello
    >>> sh("echo $GREETING")
    + echo Hello
    Hello
    0

## Design Overview

### 3 Tier Storage (1-1-1)

1. One secrets configuration file (for passwords, etc.).
2. One repository for scripts and configuration, i.e., this repository.
3. One blob repository to store all real-time data in one root directory.
   Symlinks are created to map to the system structure as needed.

This approach makes it very easy to move from one host system to another.

### Use Simple Scripts When Possible

The simplest install module is a single script. These scripts are generally
idempotent and can be run once or many times. An example would be
`apt-get update && apt-get -y upgrade`.

### Break Complicated Scripts Into Stages

More complicated install modules can broken into multiple scripts:

1. Install   - `apt-get install <foo>`
2. Prepare   - stop services, setup users, etc.
3. Configure - create/update configuration from templates
4. Copy      - copy files from backup or other store; generally only done once
5. Finalize  - start/restart services, etc.

During cold-install, the scripts are run once in order. An example of a script
that is generally only run once is the **copy** script.

Other scripts are often updated and run over and over on the production system.
An example would be the **configure** script that is run multiple times because
configuration changes often.
