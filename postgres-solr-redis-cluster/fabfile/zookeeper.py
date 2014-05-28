#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Zookeeper Configuration

Created by: Rui Carmo
"""

import os, sys
from StringIO import StringIO
from fabric.api import env, local, hosts, roles
from fabric.operations import run, sudo, put, hide, settings
from fabric.contrib.files import contains, exists, cd, append, comment, uncomment
from .helpers import tarball, collect_ip_addresses
from .config import tarballs

init_file     = '/etc/init.d/zookeeper'
defaults_file = '/etc/default/zookeeper'
config_dir    = '/etc/zookeeper'
config_file   = config_dir + '/zoo.cfg'
data_dir      = '/srv/data/zookeeper'
log_dir       = '/var/log/zookeeper'


def unpack_zookeeper():
    """Grab and unpack Zookeeper"""

    if not exists('/srv/zookeeper'):
        tarball(**tarballs['zookeeper'])
        sudo('ln -s /srv/zookeeper-3.4.5 /srv/zookeeper')


def setup_zookeeper_service():
    """Set up the Zookeeper service and configure it for the cluster"""
    
    if not exists(config_dir):
        sudo('mkdir -p ' + config_dir)
        sudo('chown root:root ' + config_dir)

    for d in [data_dir, log_dir]:
        if not exists(d):
            sudo('mkdir -p ' + d)
            sudo('chown -R www-data:www-data ' + d)

    if not exists(init_file):
        put(StringIO(zookeeper_init), init_file, use_sudo=True)
        sudo('chmod +x ' + init_file)
        sudo('chown root:root ' + init_file)

    if not exists(config_file):
        put(StringIO(zookeeper_config), config_file, use_sudo=True)

    if not exists(defaults_file):
        put(StringIO(zookeeper_defaults), defaults_file, use_sudo=True)

    append(config_file, 'initLimit=5', use_sudo=True)
    append(config_file, 'syncLimit=2', use_sudo=True)
    # production machines need to know about each other and have an ID file
    if 'production' in env.roles:
        i = 1
        for h in env.roledefs['production']:
            i = i + 1

            append(config_file, 'dataDir=/srv/data/zookeeper/%d' % i, use_sudo=True)
            append(config_file, 'server.%d=%s:2888:3888' % (i, env.addresses[h]), use_sudo=True)
        # now create the ID file
        put(StringIO(str(env.roledefs['production'].index(env.host))), "%s/myid" % data_dir, use_sudo=True)
    else:
        append(config_file, 'dataDir=/srv/data/zookeeper/1', use_sudo=True)
        append(config_file, 'server.1=127.0.0.1:2888:3888', use_sudo=True)
        put(StringIO("1"), "%s/myid" % data_dir, use_sudo=True)


    sudo('update-rc.d zookeeper defaults')
    sudo('service zookeeper restart')


zookeeper_config = """
tickTime=2000
clientPort=2181
"""

zookeeper_defaults = """
# comment this line to disable
ZOOKEEPER_ENABLED=false

ZOOKEEPER_USER=www-data

ZOOCFG=/etc/zookeeper/zoo.cfg

ZOOKEEPER_PREFIX=/srv/zookeeper

ZOO_LOG_DIR=/var/log/zookeeper
#JVMFLAGS=
"""


zookeeper_init = """#! /bin/sh

### BEGIN INIT INFO
# Provides:     zookeeper
# Required-Start:   $remote_fs $syslog
# Required-Stop:    $remote_fs $syslog
# Default-Start:    2 3 4 5
# Default-Stop:
# Short-Description:    Apache ZooKeeper server
### END INIT INFO

set -e

# /etc/init.d/zookeeper: start and stop the Apache ZooKeeper daemon

umask 022

. /etc/default/zookeeper

ZOOBINDIR=${ZOOKEEPER_PREFIX}/bin
ZOODATADIR=$(grep "^[[:space:]]*dataDir=" "$ZOOCFG" | sed -e 's/.*=//')
export ZOOPIDFILE=${ZOODATADIR}/zookeeper_server.pid

# stupid hack to workaround the release's buggy startup scripts
export ZOO_LOG_DIR=${ZOO_LOG_DIR}
cd ${ZOO_LOG_DIR}

test -x $JAVA || exit 0

if [ ! ${ZOOKEEPER_ENABLED} ]; then
    exit 0
fi

. /lib/lsb/init-functions

case "$1" in
  start)
    log_daemon_msg "Starting Apache ZooKeeper server" "zookeeper"
    if start-stop-daemon --start --quiet --oknodo --pidfile ${ZOOPIDFILE} -c ${ZOOKEEPER_USER} -x ${ZOOKEEPER_PREFIX}/bin/zkServer.sh start ${ZOOCFG}; then
        log_end_msg 0
    else
        log_end_msg 1
    fi
    ;;
  stop)
    log_daemon_msg "Stopping Apache ZooKeeper server" "zookeeper"
    if start-stop-daemon --stop --quiet --oknodo --pidfile ${ZOOPIDFILE}; then
        log_end_msg 0
    else
        log_end_msg 1
    fi
    ;;

  restart)
    log_daemon_msg "Restarting Apache ZooKeeper server" "zookeeper"
    start-stop-daemon --stop --quiet --oknodo --retry 30 --pidfile ${ZOOPIDFILE}
    if start-stop-daemon --start --quiet --oknodo --pidfile ${ZOOPIDFILE} -c ${ZOOKEEPER_USER} -x ${ZOOKEEPER_PREFIX}/bin/zkServer.sh start ${ZOOCFG}; then
        log_end_msg 0
    else
        log_end_msg 1
    fi
    ;;

  status)
    status_of_proc -p ${ZOOPIDFILE} ${JAVA} zookeeper && exit 0 || exit $?
    ;;

  *)
    log_action_msg "Usage: /etc/init.d/zookeeper {start|stop|restart|status}"
    exit 1
esac

exit 0
"""
