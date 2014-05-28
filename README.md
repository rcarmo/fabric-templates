fabric-templates
================

Sets of Fabric modules for cloud deployments on AWS, Azure, etc.

Contains supporting functions for:

* Deploying various sets of packages to Debian-based Linux machines, including setting up remote repositories, downloading packages (and tarballs) and gathering IP addresses from all interfaces
* Deploying a Postgres cluster from scratch, including IP address re-binding, bootstrapping a database and enabling replication
* Deploying a Redis server, including IP address re-binding and password setup
* Deploying a Solr Cloud instance, including setting up init scripts, Zookeeper and other arcane tweaks.

The example deployment(s) can be easily broken down and re-used for other setups.
