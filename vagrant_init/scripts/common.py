#!/usr/bin/env python

import datetime
import grp
import pwd
import os
import string
import subprocess
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config

SCRIPT_BASE = os.path.dirname(__file__)

if config.LOGGING:
    LOG_PATH = "/tmp/btb-install-%s.log" % datetime.datetime.now().strftime('%Y%m%d')
    LOG_FILE = open(LOG_PATH, "a+")

def log(data, append_newline=True):
    if append_newline:
        data = data + "\n"
    sys.stdout.write(data)
    sys.stdout.flush()
    if config.LOGGING:
        LOG_FILE.write(data)

def run(*args):
    proc = subprocess.Popen(args, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    while True:
        data = proc.stdout.readline()
        if data == '':
            break
        log(data, append_newline=False)
    proc.communicate()
    return proc.returncode

def sh(command, with_config=True, exit_on_error=True, print_commands=True, require_success=True):
    if with_config:
        command = interpolate(command)
    if print_commands:
        command = "set -x\n" + command
    if exit_on_error:
        command = "set -e\n" + command
    result = run('/bin/bash', '-c', command)
    if require_success and result != 0:
        log("Exiting on error %d\n" % result)
        sys.exit(result)
    else:
        return result

def script(script_name, with_config=False, print_commands=False):
    log("+")
    log("+ Running script %s" % script_name)
    log("+")
    return sh(os.path.join(SCRIPT_BASE, script_name),
        with_config=with_config, print_commands=print_commands)

def config_dict():
    dct = {}
    for name in dir(config):
        if not name.startswith("_"):
            value = getattr(config, name)
            if type(value) != types.ModuleType:
                dct[name] = value
    return dct

def interpolate(template, extra_context=None):
    context = config_dict()
    if extra_context:
        context.update(extra_context)
    return string.Template(template).safe_substitute(context)

def write_template(destination, source=None, source_host='common',
                                owner="root", group="root", perms="0644",
                                extra_context=None):
    if source is None:
        source = "%s%s" % (source_host, destination)
    log("+")
    log("+ Writing template %s" % source)
    log("+               to %s" % destination)
    log("+               as %s:%s %s" % (owner, group, perms))
    log("+")

    with open(os.path.join(SCRIPT_BASE, "..", "templates", source)) as fh:
        template = fh.read()

    if not os.path.exists(os.path.dirname(destination)):
        os.makedirs(os.path.dirname(destination))

    with open(destination, 'w') as fh:
        os.chmod(destination, int(perms, 8))
        uid = pwd.getpwnam(owner).pw_uid
        gid = grp.getgrnam(group).gr_gid
        os.chown(destination, uid, gid)
        fh.write(interpolate(template, extra_context))
    return True

def create_postgres_user(username, password):
    # Create user, unless it already exists.
    sh(r"""
        su postgres -c "psql -c \"CREATE USER {user} WITH PASSWORD '{password}';\""
    """.format(user=username, password=password),
    with_config=False, require_success=False)

def create_postgres_database(owner, dbname):
    # Create database, unless it already exists.
    sh('su postgres -c "createdb -O {user} {dbname}"'.format(
        user=owner,
        dbname=dbname
    ), require_success=False)
