#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Main fabric module

This sets up a Postgres cluster across three boxes that supports a Python application.
The app relies on a shared Redis server and spawns tasks on all 3 machines, and uses Solr for maintaining a supporting index.

Created by: Rui Carmo
"""

import os, sys, time, logging
from fabric.api import env, local, hosts, roles, execute
from fabric.operations import run, sudo, put, hide, settings
from fabric.contrib.files import contains, exists, cd, append, comment
from fabric.contrib.project import rsync_project
from StringIO import StringIO

from .config import repos, packages, tarballs
from .helpers import tarball, psql, collect_ip_addresses, inject_files
from .debian import setup_repo, install, pip_install
from .postgres import rebind_postgres, setup_database, setup_master, setup_slaves
from .redis import rebind_redis, lockdown_redis
from .solr import unpack_solr, setup_solr_service, setup_solr_master, setup_solr_slave, upload_solr_collection
from .zookeeper import unpack_zookeeper, setup_zookeeper_service


# We assume we'll have 3 boxes in production, one master and two slaves
env.roledefs = {
    'development' : ['localhost'],
    'production'  : ['box1', 'box2', 'box3'],
    'master'      : ['box1'],
    'slaves'      : ['box2', 'box3']
}
env.addresses = {}


# Test our local (Python) app
def test():
    local("nosetests")


# Deploy our shared redis, re-binding it to the network interfaces and locking it down with a password
def shared_redis():
    execute(collect_ip_addresses,hosts=env.roledefs['production'])
    execute(rebind_redis)
    execute(lockdown_redis)


# Deploy our postgres cluster, re-binding the network interfaces too
def postgres_cluster():
    execute(collect_ip_addresses,hosts=env.roledefs['production'])
    execute(rebind_postgres)
    execute(setup_database, hosts=env.roledefs['production'])
    execute(setup_master,   hosts=env.roledefs['master'])
    execute(setup_slaves,   hosts=env.roledefs['slaves'])
    

# Deploy Solr
def solr_cluster():
    execute(collect_ip_addresses,hosts=env.roledefs['production'])
    execute(unpack_solr,hosts=env.roledefs['production'])
    execute(setup_solr_service, hosts=env.roledefs['production'])
    execute(setup_solr_master, hosts=env.roledefs['master'])
    execute(setup_solr_slave, hosts=env.roledefs['slaves'])


# Deploy Zookeeper
def zookeeper_cluster():
    execute(unpack_zookeeper, hosts=env.roledefs['production'])
    execute(setup_zookeeper_service, hosts=env.roledefs['production'])


# Deploy base packages to all machines
@roles('production')
def setup_environment():
    with hide('running','output','warnings'):
        setup_repo(repos['pgdg'])
        setup_repo(repos['dotdeb'])
        apt_update()
        map(install,packages['postgres'])
        map(install,packages['redis'])
        map(install,packages['base'])
        map(install,packages['python'])
        pip_install(packages['pip'])
        inject_files(configuration_files)
    shared_redis()
    postgres_cluster()


# Deploy our project
@roles('production')
def deploy_project():
    rsync_project(remote_dir='/srv/project', delete=True, exclude='.git')

