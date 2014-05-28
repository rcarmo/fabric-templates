#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Postgres Configuration

Supporting routines for deploying and provisioning a Postgres cluster

TODO: replace 'project' below with a value taken from .config

Created by: Rui Carmo
"""

import os, sys, time
from fabric.api import env, local, hosts, roles
from fabric.operations import run, sudo, put, hide, settings
from fabric.contrib.files import contains, exists, cd, append, comment
from .helpers import psql, collect_ip_addresses

prefix        = '/etc/postgresql/9.2/main/%s'
pg_conf       = prefix % 'postgresql.conf'
hba_conf      = prefix % 'pg_hba.conf'
data_path     = '/var/lib/postgresql/9.2/main'
recovery_conf = data_path + '/recovery.conf'


@roles('production')
def rebind_postgres(intf='eth0'):
    """Bind postgres to eth0 besides localhost"""
    collect_ip_addresses(intf)
    if not contains(pg_conf,'^listen_addresses'):
        append(pg_conf,"listen_addresses = 'localhost,%s'" % env.addresses[env.host][intf], use_sudo = True)
        sudo('service postgresql restart')


def setup_database():
    """Create the application database and associated user with a temporary password"""
    with hide('output', 'running'):
        with settings(warn_only=True):
            psql("CREATE USER project UNENCRYPTED PASSWORD 'project';")
            psql("ALTER ROLE project REPLICATION LOGIN;")
        with settings(warn_only=True):
            psql("CREATE DATABASE project ENCODING 'UTF-8';")
        psql("GRANT ALL ON DATABASE project TO project;")


def setup_master():
    print "Setting up master %s" % env.host
    sudo('service postgresql stop')
    append(pg_conf, 'wal_level = hot_standby', use_sudo = True)
    append(pg_conf, 'max_wal_senders = 5', use_sudo = True)
    append(pg_conf, 'wal_keep_segments = 32', use_sudo = True)
    append(pg_conf, 'max_connections = 1000', use_sudo = True)

    if not contains(hba_conf, 'replication'):
        for host in env.roledefs['slaves']:
            if host not in env.addresses:
                raise KeyError("could not find slave IP address")
            append(hba_conf, 'host  replication   all   %s/32      trust' % env.addresses[host]['eth0'], use_sudo = True)
            append(hba_conf, 'host  all   all   %s/32      md5' % env.addresses[host]['eth0'], use_sudo = True)

    sudo('service postgresql start')


def setup_slaves():
    print "Setting up slave %s" % env.host
    with settings(warn_only=True):
        sudo('service postgresql stop')

    host = env.roledefs['master'][0]
    if host not in env.addresses:
        raise KeyError("could not find master IP address")
    print host
    master_ip = env.addresses[host]['eth0']

    append(pg_conf, 'wal_level = hot_standby', use_sudo = True)
    append(pg_conf, 'max_wal_senders = 5', use_sudo = True)
    append(pg_conf, 'wal_keep_segments = 32', use_sudo = True)
    append(pg_conf, 'hot_standby = on', use_sudo = True)
    
    with cd(os.path.dirname(data_path)):
        with settings(warn_only=True):
            sudo('mv main main.%d' % time.time() )
        print "Starting backup from master %s" % master_ip
        sudo('pg_basebackup -P -x -h %s -U project -D main' % master_ip)
        sudo('rm -f main/backup_label')
        sudo('chown -R postgres:postgres main')
        print "Done."
    append(recovery_conf, "standby_mode = 'on'", use_sudo = True)
    append(recovery_conf, "primary_conninfo = 'host=%s user=project'" % master_ip, use_sudo = True)
    sudo('service postgresql start')


@roles('master')
def rsync_data():
    """Unfinished stub for replicating data to new members of the cluster"""
    print "Syncing data to slaves"
    #rsync -av --rsync-path="sudo rsync" --exclude pg_xlog --exclude postgresql.conf /var/lib/* 192.168.0.1:/var/lib/postgresql/data/
