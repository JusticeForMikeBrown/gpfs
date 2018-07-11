GPFS Utilities
===============

In this repository you will find some Python wrapper scripts meant to aid in administration of GPFS quotas.

**changequota.py** allows power-users to modify user-level quota within centrally-managed filesets.

**gpfs_quotas_table.py** will print filesets and user-level quotas

**newgpfsdir.py** allows power-users to create new directories on GPFS file systems.  Useful when top-level fileset directories are owned by root.

**myquota** allows user to check their quota without needing to actually explicitly run gpfs_quotas_table.py

**myquota_sudoers** contains a possible sudo configuration for myquota bash wrapper script

**newgpfsdir_sudoers** contains a possible sudo configuration for newgpfsdir.py script


Requirements
------------

You must be using Python 3.6

CentOS 7 users could try [IUS](https://centos7.iuscommunity.org/ius-release.rpm)

[Tabulate](https://pypi.org/project/tabulate/)

[Slackclient](https://pypi.org/project/slackclient/)
