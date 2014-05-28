#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Configuration

This file contains shared constants/dictionaries for the fabfile

Created by: Rui Carmo
"""

# copy our configuration files to a specific location and set permissions
# (this is a sample for an old Postgres deployment)
skel = {
    'postgres': [{
        'path': '/etc/postgresql/9.2',
        'owner': 'postgres:postgres',
        'perms': '0644',
        'recursive': True
    }, {
        'path': '/etc/postgresql/9.2/main/pg_hba.conf',
        'owner': 'postgres:postgres',
        'perms': '0644'
    }, {
        'path': '/etc/postgresql/9.2/main/pg_ident.conf',
        'owner': 'postgres:postgres',
        'perms': '0640'
    }]
}

# External APT repositories
# these are the ones I commonly use for Postgres and Redis on Debian
repos = {
    # Postgres repo
    "pgdg": {
        "key_name"   : "PostgreSQL Debian Repository",
        "key_url"    : "http://apt.postgresql.org/pub/repos/apt/ACCC4CF8.asc",
        "source_file": "deb http://apt.postgresql.org/pub/repos/apt/ wheezy-pgdg main"
    },
    # Redis repo
    "dotdeb": {
        "key_name"   : "dotdeb.org",
        "key_url"    : "http://www.dotdeb.org/dotdeb.gpg",
        "source_file": "deb http://mirrors.fe.up.pt/dotdeb/ wheezy all"
    }
}


# Package groups I usually deploy on servers
packages = {
    "base"    : ['vim', 'htop', 'tmux', 'wget', 'netcat', 'rsync', 'bmon', 'speedometer', 'jpegoptim', 'imagemagick'],
    "postgres": ['postgresql-9.2', 'postgresql-client-9.2', 'libpq-dev'],
    "redis"   : ['redis-server'],
    "python"  : ['python2.7-dev', 'libevent-dev', 'python-setuptools'],
    "java"    : ['openjdk-7-jre-headless'],
    "pip"     : [
        "gunicorn==0.17.4",
        "gevent==0.13.8",
        "psycopg2==2.5",
        "Pygments==1.6",
        "celery-with-redis==3.0",
        "nose==1.3.0",
        "flower==0.5.1"
    ]
}


tarballs = {
    "solr": {
        'url'   : 'http://mirrors.fe.up.pt/pub/apache/lucene/solr/4.4.0/solr-4.4.0.tgz',
        'target': '/srv'
    },
    "zookeeper": {
        'url'   : 'http://mirrors.fe.up.pt/pub/apache/zookeeper/zookeeper-3.4.5/zookeeper-3.4.5.tar.gz',
        'target': '/srv'
    }
}

configuration_files = {
    "/etc/profile.d/ourenv.sh": 'export OURSETTING1=OURVALUE1\nexport OURSETTING2=OURVALUE2'
}
