#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Solr Configuration

Support functions for setting up a Solr Cloud environment (tested on Solr 4.0)

Created by: Rui Carmo
"""

import os, sys
from StringIO import StringIO
from fabric.api import env, local, hosts, roles
from fabric.operations import run, sudo, put, hide, settings
from fabric.context_managers import lcd
from fabric.contrib.files import contains, exists, cd, append, comment, uncomment
from fabric.contrib.project import rsync_project
from .helpers import tarball, collect_ip_addresses
from .config import tarballs

init_file     = '/etc/init.d/solr'
defaults_file = '/etc/default/solr'
data_dir      = '/srv/data/solr'



# Download and install the Solr tarball
def unpack_solr():
    if not exists('/srv/solr'):
        tarball(**tarballs['solr'])
        sudo('ln -s /srv/solr-4.4.0 /srv/solr')


# Deploy a Solr init script
def setup_solr_service():
    if not exists(init_file):
        put(StringIO(solr_init), init_file, use_sudo=True)
        sudo('chmod +x ' + init_file)
        sudo('chown root:root ' + init_file)

    if not exists(defaults_file):
        put(StringIO(solr_defaults), defaults_file, use_sudo=True)

    if not exists(data_dir):
        sudo('mkdir -p ' + data_dir)
        sudo('chown -R www-data:www-data ' + data_dir)

    # make sure all example paths are usable by www-data
    sudo('update-rc.d solr defaults')
    sudo('service solr restart')


def setup_solr_master():
    uncomment(defaults_file, 'SOLR_LOCAL_ZOOKEEPER', use_sudo=True)
    sudo('service solr restart')


def setup_solr_slave():
    host = env.roledefs['master'][0]
    if host not in env.addresses:
        raise KeyError("could not find master IP address")
    print host
    master_ip = env.addresses[host]['eth0']
    append(defaults_file, 'SOLR_REMOTE_ZOOKEEPER=%s:9983' % master_ip, use_sudo=True)
    sudo('service solr restart')


def upload_solr_collection():
    # upload a pre-build Solr collection
    with cd(data_dir):
        sudo('chmod -R a+w .')
    rsync_project(data_dir, local_dir = 'deploy/production/solr_data/')
    with cd(data_dir):
        sudo('chmod -R a-w .')
        sudo('chown -R www-data:www-data project')


solr_defaults = """
# comment this to prevent Solr from starting
SOLR_ENABLED=true

# uncomment this to run a local master/zookeper
SOLR_LOCAL_ZOOKEEPER=true

# uncomment this to run a local slave with a remote zookeper
#SOLR_REMOTE_ZOOKEEPER=localhost:2181

# number of data shards (1 for mirroring, 2 for splitting, etc.)
SOLR_NUM_SHARDS=1

SOLR_USER=www-data

SOLR_COLLECTION=project

SOLR_DATA_DIR=/srv/data/solr/project

SOLR_BOOTSTRAP=
"""

solr_init = """#! /bin/sh

### BEGIN INIT INFO
# Provides:             solr
# Required-Start:       $remote_fs $syslog
# Required-Stop:        $remote_fs $syslog
# Default-Start:        2 3 4 5
# Default-Stop:         0 1 6
# Short-Description:    Apache Solr
### END INIT INFO

# Starts, stops, and restarts solr

. /etc/default/solr

# This is required to set jetty.home and have the WAR expanded properly
SOLR_DIR=/srv/solr/example
LOG_FILE=/var/log/solr.log
JAVA=/usr/bin/java

PRIVSEP_DIR=/var/run/solr
PID_FILE=${PRIVSEP_DIR}/solr.pid

check_privsep_dir() {
    # Create the PrivSep empty dir if necessary
    if [ ! -d ${PRIVSEP_DIR} ]; then
    mkdir -p ${PRIVSEP_DIR}
        chown ${SOLR_USER}:${SOLR_USER} ${PRIVSEP_DIR}
    chmod 0775 ${PRIVSEP_DIR} 
    fi
}

check_log_dir() {
    if [ ! -d ${SOLR_DIR}/logs ]; then
        mkdir -p ${SOLR_DIR}/logs
    fi
    chown -R $SOLR_USER:$SOLR_USER "$SOLR_DIR/logs"
}

check_runtime_dir() {
    chown -R $SOLR_USER:$SOLR_USER "$SOLR_DIR/solr-webapp"
    chown -R $SOLR_USER:$SOLR_USER "$SOLR_DATA_DIR"
}

test -x $JAVA || exit 0
test -x $SOLR_DIR || exit 0

# check if various defaults are set

if [ ! ${SOLR_ENABLED} ]; then
    exit 0
fi

touch $LOG_FILE
chown $SOLR_USER:$SOLR_USER $LOG_FILE

if [ $SOLR_LOCAL_ZOOKEEPER ]; then
    SOLR_CLOUD_OPTIONS="-DzkRun -DnumShards=${SOLR_NUM_SHARDS} -Dbootstrap_confdir=${SOLR_DATA_DIR}/conf -Dcollection.configName=${SOLR_COLLECTION}"
    # Create storage path for Zookeper data
    if [ ! -e "$SOLR_DATA_DIR/../zoo_data" ]; then
        mkdir "$SOLR_DATA_DIR/../zoo_data"
        chown -R $SOLR_USER:$SOLR_USER "$SOLR_DATA_DIR/../zoo_data"
    fi
else
    SOLR_CLOUD_OPTIONS="-DzkHost=${SOLR_REMOTE_ZOOKEEPER} -Dbootstrap_confdir=${SOLR_DATA_DIR}/conf -Dcollection.configName=${SOLR_COLLECTION}"
fi

JAVA_OPTIONS="-Xmx256m -jar -Djetty.home=${SOLR_DATA_DIR} -Dsolr.solr.home=${SOLR_DIR} ${SOLR_DIR}/start.jar $SOLR_CLOUD_OPTIONS"

. /lib/lsb/init-functions

umask 011

case $1 in
    start)
        echo "Starting Solr"
        check_privsep_dir
        check_log_dir
        check_runtime_dir
        cd $SOLR_DATA_DIR
        log_daemon_msg "Starting Apache Solr" "solr"
        if start-stop-daemon --start --quiet --background --make-pidfile --chdir $SOLR_DATA_DIR --pidfile $PID_FILE --chuid $SOLR_USER --exec $JAVA -- $JAVA_OPTIONS 2>&1 >> $LOG_FILE; then
            log_end_msg 0
        else
            log_end_msg 1
        fi
        ;;
    stop)
        echo "Stopping Solr"
        cd $SOLR_DATA_DIR
        log_daemon_msg "Stopping Apache Solr" "solr"
        start-stop-daemon --stop --quiet --pidfile $PID_FILE --retry 30
        ;;
    restart)
        check_privsep_dir
        check_log_dir
        check_runtime_dir
        log_daemon_msg "Restarting Apache Solr" "solr"
        $0 stop
        sleep 1
        $0 start
        ;;
    status)
        status_of_proc -p $PID_FILE $JAVA && exit 0 || exit $?
        ;;

     *)
        log_action_msg "Usage: /etc/init.d/solr {start|stop|restart|status}"
        exit 1
esac

exit 0
"""
