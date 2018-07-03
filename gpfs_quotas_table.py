#!/usr/bin/env python3.6
__author__ = 'quackmaster@protonmail.com'

import argparse
import pwd
import os
import sys
import subprocess
import re
from tabulate import tabulate

support = 'support@dev.null'

parser = argparse.ArgumentParser()
parser.add_argument('filesystem',  help='gpfs filesystem to check')
parser.add_argument('user',  help='user to check')
print("\nThis script checks your GPFS fileset usage and prints centrally-managed fileset quotas. \n")
print("It will also print user-level quotas within filesets if they exist. \n")
print("For assistance contact", __author__, "or" , support +"." "\n")
args = parser.parse_args()


#global vars
user = sys.argv[2]
fs = '/dev/' + sys.argv[1]

# ensure running on gpfs node
def gpfs_node():
    try:
        file = open('/var/adm/ras/mmfs.log.latest', 'r')
    except IOError:
        print("You must run this script on a GPFS node!")
        sys.exit()

gpfs_node()    

# ensure running as root / sudo
def privs():

    if os.getuid() == 0:
        print("Checking fileset usage and quota for user", sys.argv[2], "on filesystem", sys.argv[1] + ":","\n \n")
    else:
        print("You must run with sudo!", "\n \n""Contact", support, "for assistance.")
        sys.exit()
privs()

# ensure user exists
def checkuser():
    try:
        pwd.getpwnam(user)
    except KeyError:
        print("User", user, "does not exist.")
        sys.exit()

checkuser()

# the main function
def quota():

    fsc = 'mmrepquota ' + fs + ' --block-size=auto | grep '
    awkc = " | awk ' { print $1 \"     \" $2 \"          \" $4 } '"

    getfileset_command = fsc + user + awkc
    
# below commands get a list of filesets where user owns data as well the amount

    c1 = subprocess.run(getfileset_command, timeout=5, shell=True, stdout=subprocess.PIPE)
    c2 = c1.stdout.decode('utf-8').split()

    fileset_list = []
    for string in c2:
        match = re.search(r'(?:store|scratch)', string)
        if match:
            fileset_list.append(string)
     
# below commands get fileset quotas for all filesets that contain user data
# it does not show fileset utilization

    fsq = []
    for item in fileset_list:

        fileset_check = 'mmlsquota -j ' + item + ' /dev/athena --block-size=auto | '
        awkfs_c = " awk ' { print $4 } ' | tail -n 1 "
        getfileset_quota_command = fileset_check + awkfs_c

        c4 = subprocess.run(getfileset_quota_command, timeout=5, shell=True, stdout=subprocess.PIPE)
        c5 = c4.stdout.decode('utf-8').split()
        #print(c4.stdout)
        #print(c5)
        for string in c5:
            fsq.append(string)

# fileset utilization gathered below

    fsu = []

    for item in fileset_list:
        fsu_check = 'mmlsquota --block-size=auto -j '
        fsu_awk = " | awk ' { print $3 } ' | tail -n 1"
        fsu_command = fsu_check + item + ' ' + fs +  fsu_awk

        c6 = subprocess.run(fsu_command, timeout=5, shell=True, stdout=subprocess.PIPE)
        c7 = c6.stdout.decode('utf-8').split()

        for string in c7:
            fsu.append(string)

# count number of filesets

    size = len(fileset_list)

# below gets a list of user quotas on filesets where users own data

    uq = []

    for item in fileset_list:
        uq_check = 'mmlsquota -u  ' + user + ' athena:' + item + ' --block-size=auto |'
        uq_awk = "awk ' { print $5 } ' | tail -n 1"
        uq_command = uq_check + uq_awk

        c8 = subprocess.run(uq_command, timeout=5, shell=True, stdout=subprocess.PIPE)
        c9 = c8.stdout.decode('utf-8').split()

        for string in c9:
            match = re.search(r'(T)', string)
            if match:
                uq.append(string)

# count number of user quotas
    uq_size = len(uq)

# user utilization on fileset, along with fileset quota, printed below

    # zero filesets
    if size == 0:
        if uq_size == 0:
            one_fileset = ['fileset', 'usage']
            data = tabulate(dict(zip([c2[1],c2[2]], one_fileset)), headers="keys", tablefmt="orgtbl")
            print(data)
        else:
           one_fileset = ['fileset', 'usage']
           data = tabulate(dict(zip([c2[1],c2[2]], one_fileset)), headers="keys", tablefmt="orgtbl")
           print(data)

    # one fileset
    if size == 1:
        if uq_size == 1:
            one_fileset = ['fileset', 'usage', 'filesetquota']
            data = tabulate(dict(zip([c2[1],c2[2],fsq[0]], one_fileset)), headers="keys", tablefmt="orgtbl")
            print(data)

        else:
            one_fileset = ['fileset', 'usage', 'filesetquota']
            data = tabulate(dict(zip([c2[1],c2[2],fsq[0]], one_fileset)), headers="keys", tablefmt="orgtbl")
            print(data)

    # two filesets
    if size == 2:
        
        # no user quotas
        if uq_size == 0:
            two_filesets = ['fileset', 'filesetquota', 'filesetusage', 'myusage', 'fileset', 'filesetquota', 'filesetusage', 'myusage']
            c3 = c2.pop(3)
            data = tabulate(dict(zip([c2[1],fsq[0],fsu[0],c2[2],c2[3],fsq[1],fsu[1],c2[4]], two_filesets)), headers="keys", tablefmt="orgtbl")
            print(data)

        # one user quota
        if uq_size == 1:
            two_filesets = ['fileset', 'filesetquota', 'usage', 'userquota', 'fileset', 'filesetquota', 'usage']
            c3 = c2.pop(3)
            data = tabulate(dict(zip([c2[1],fsq[0],c2[2],uq[0],c2[3],fsq[1],c2[4]], two_filesets)), headers="keys", tablefmt="orgtbl")
            print(data)

        # two user quotas
        if uq_size == 2:
            two_filesets = ['fileset', 'filesetquota', 'usage', 'userquota', 'fileset', 'filesetquota', 'usage', 'userquota']
            c3 = c2.pop(3)
            data = tabulate(dict(zip([c2[1],fsq[0],c2[2],uq[0],c2[3],fsq[1],c2[4]],uq[1], two_filesets)), headers="keys", tablefmt="orgtbl")
            print(data)

    # three filesets
    if size == 3:
        if uq_size == 0:
        
            three_filesets = ['fileset', 'filesetquota', 'usage', 'fileset ', 'filesetquota', 'usage', 'fileset', 'filesetquota', 'usage']
            # delete first user dup
            c3 = c2.pop(3)
            # delete second user dup
            c3 = c2.pop(5)
            data = tabulate(dict(zip([c2[1],fsq[0],c2[2],c2[3],fsq[1],c2[4],c2[5],fsq[2],c2[6]], three_filesets)), headers="keys", tablefmt="orgtbl")
            print(data)

        if uq_size == 1:
        
            three_filesets = ['fileset', 'filesetquota', 'usage', 'userquota', 'fileset ', 'filesetquota', 'usage', 'fileset', 'filesetquota', 'usage']
            # delete first user dup
            c3 = c2.pop(3)
            # delete second user dup
            c3 = c2.pop(5)
            data = tabulate(dict(zip([c2[1],fsq[0],c2[2],uq[0],c2[3],fsq[1],c2[4],c2[5],fsq[2],c2[6]], three_filesets)), headers="keys", tablefmt="orgtbl")
            print(data)

        if uq_size == 2:
        
            three_filesets = ['fileset', 'filesetquota', 'usage', 'userquota', 'fileset ', 'filesetquota', 'usage', 'userquota', 'fileset', 'filesetquota', 'usage']
            # delete first user dup
            c3 = c2.pop(3)
            # delete second user dup
            c3 = c2.pop(5)
            data = tabulate(dict(zip([c2[1],fsq[0],c2[2],uq[0],c2[3],fsq[1],c2[4],uq[1],c2[5],fsq[2],c2[6]], three_filesets)), headers="keys", tablefmt="orgtbl")
            print(data)

        if uq_size == 3:
        
            three_filesets = ['fileset', 'filesetquota', 'usage', 'userquota', 'fileset ', 'filesetquota', 'usage', 'userquota', 'fileset', 'filesetquota', 'usage', 'userquota']
            # delete first user dup
            c3 = c2.pop(3)
            # delete second user dup
            c3 = c2.pop(5)
            data = tabulate(dict(zip([c2[1],fsq[0],c2[2],uq[0],c2[3],fsq[1],c2[4],uq[1],c2[5],fsq[2],c2[6],uq[2]], three_filesets)), headers="keys", tablefmt="orgtbl")
            print(data)

    # four filesets
    if size == 4:
        if uq_size == 0:
        
            four_filesets = ['fileset', 'filesetquota', 'usage', 'fileset ', 'filesetquota', 'usage', 'fileset', 'filesetquota', 'usage', 'fileset', 'filesetquota', 'usage']
            # delete first user dup
            c3 = c2.pop(3)
            # delete second user dup
            c3 = c2.pop(5)
            c3 = c2.pop(7)
            data = tabulate(dict(zip([c2[1],fsq[0],c2[2],c2[3],fsq[1],c2[4],c2[5],fsq[2],c2[6],c2[7],fsq[3],c2[8]], four_filesets)), headers="keys", tablefmt="orgtbl")
            print(data)

        if uq_size == 1:
        
            four_filesets = ['fileset', 'filesetquota', 'usage', 'userquota', 'fileset ', 'filesetquota', 'usage', 'fileset', 'filesetquota', 'usage', 'fileset', 'filesetquota', 'usage']
            # delete first user dup
            c3 = c2.pop(3)
            # delete second user dup
            c3 = c2.pop(5)
            c3 = c2.pop(7)
            data = tabulate(dict(zip([c2[1],fsq[0],c2[2],uq[0],c2[3],fsq[1],c2[4],c2[5],fsq[2],c2[6],c2[7],fsq[3],c2[8]], four_filesets)), headers="keys", tablefmt="orgtbl")
            print(data)

        if uq_size == 2:
        
            four_filesets = ['fileset', 'filesetquota', 'usage', 'userquota', 'fileset ', 'filesetquota', 'usage', 'userquota', 'fileset', 'filesetquota', 'usage', 'fileset', 'filesetquota', 'usage']
            # delete first user dup
            c3 = c2.pop(3)
            # delete second user dup
            c3 = c2.pop(5)
            c3 = c2.pop(7)
            data = tabulate(dict(zip([c2[1],fsq[0],c2[2],uq[0],c2[3],fsq[1],c2[4],uq[1],c2[5],fsq[2],c2[6],c2[7],fsq[3],c2[8]], four_filesets)), headers="keys", tablefmt="orgtbl")
            print(data)

        if uq_size == 3:
        
            four_filesets = ['fileset', 'filesetquota', 'usage', 'userquota', 'fileset ', 'filesetquota', 'usage', 'userquota', 'fileset', 'filesetquota', 'usage', 'userquota', 'fileset', 'filesetquota', 'usage']
            # delete first user dup
            c3 = c2.pop(3)
            # delete second user dup
            c3 = c2.pop(5)
            c3 = c2.pop(7)
            data = tabulate(dict(zip([c2[1],fsq[0],c2[2],uq[0],c2[3],fsq[1],c2[4],uq[1],c2[5],fsq[2],c2[6],uq[2],c2[7],fsq[3],c2[8]], four_filesets)), headers="keys", tablefmt="orgtbl")
            print(data)

        if uq_size == 4:
            four_filesets = ['fileset', 'filesetquota', 'usage', 'userquota', 'fileset ', 'filesetquota', 'usage', 'userquota', 'fileset', 'filesetquota', 'usage', 'userquota', 'fileset', 'filesetquota', 'usage', 'userquota']
            # delete first user dup
            c3 = c2.pop(3)
            # delete second user dup
            c3 = c2.pop(5)
            c3 = c2.pop(7)
            data = tabulate(dict(zip([c2[1],fsq[0],c2[2],uq[0],c2[3],fsq[1],c2[4],uq[1],c2[5],fsq[2],c2[6],uq[2],c2[7],fsq[3],c2[8],uq[3]], four_filesets)), headers="keys", tablefmt="orgtbl")
            print(data)

quota()

