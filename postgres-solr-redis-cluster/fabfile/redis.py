#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Redis Configuration

Support functions for managing a Redis server

Created by: Rui Carmo
"""

import os, sys, time
from fabric.api import env, local, hosts, roles
from fabric.operations import run, sudo, put, hide, settings
from fabric.contrib.files import contains, exists, cd, append, comment
from .helpers import psql, collect_ip_addresses

prefix        = '/etc/redis/%s'
redis_conf     = prefix % 'redis.conf'

@roles('production')
def rebind_redis():
    """Bind redis to all interfaces"""
    comment(redis_conf,"^bind", use_sudo=True)
    sudo('service redis-server restart')


@roles('production')
def lockdown_redis(password='project'):
    """Lockdown redis with a temporary password"""
    append(redis_conf,"requirepass %s" % password, use_sudo = True)
    sudo('service redis-server restart')
