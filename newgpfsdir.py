#!/usr/bin/env python3.6

__author__ = 'quackmaster@protonmail.com'

import argparse
import pwd
import grp
import os
import shutil
import sys
from slackclient import SlackClient

support = 'help@dev.null'

parser = argparse.ArgumentParser()
parser.add_argument('path',  help='location on gpfs filesystem where new directory will be created')
parser.add_argument('directory',  help='directory to create under path')
parser.add_argument('owner',  help='user that owns the new directory')
parser.add_argument('group',  help='group that owns new directory')
print("\nThis script allows authorized power users to create new directories under GPFS filesystems managed by the SCU.\n")
print("For assistance contact", __author__, "or" , support +"." "\n")
args = parser.parse_args()

# global vars
path = sys.argv[1]
newdir = sys.argv[2]
owner = sys.argv[3]
group = sys.argv[4]

# get user who ran script using sudo
runas_user = os.environ['SUDO_USER']

# slack variables
#
#token thus this script must not be readable by normal users 
# also do not send this variable into gitlab
#slack_token = os.environ["QUOTA_TOKEN"]

slack_token = "blahtoken"
sc = SlackClient(slack_token)

# slack messages sent 
msg = runas_user + ' created new directory ' + path + '/' + newdir
emsg = runas_user + ' could NOT create directory ' + path + '/' + newdir + ' due error - please contact ' + support

# list of power users and defined filesets where user quotas can be set
lab = [ 'poweruser', '/gpfs/location/for/new/dir' ]

# only allow valid path to be chosen
def sanitize():

    if path == lab[1]:
        print("Valid path chosen\n")
    else:
        print("You must choose a valid path.  Exiting...")
        sys.exit()

sanitize()

# ensure running this script on gpfs node
def gpfs_node():
    try:
        file = open('/var/adm/ras/mmfs.log.latest', 'r')
    except IOError:
        print("You must run this script on a GPFS node!")
        sys.exit()

gpfs_node()    

# ensure user owner of newdir actually exists
def checkuser():
    try:
        pwd.getpwnam(owner)
    except KeyError:
        print("User", owner, "does not exist.")
        sys.exit()

checkuser()

# ensure group owner of newdir actually exists
def checkgroup():
    try:
        grp.getgrnam(group)
    except KeyError:
        print("Group", group, "does not exist.")
        sys.exit()

checkgroup()

def privs():

    if runas_user == lab[0]:
        print("Creating new directory", newdir, "at location", path + "\n")
    elif os.getuid() == 0:
        print("Creating new directory", newdir, "at location", path + "\n")
    else:
        print("You must run with sudo!", "\n \n""Contact", support, "for assistance.")
        sys.exit()
privs()

def createdir():
    
    ndir = path + '/' + newdir

    if not os.path.exists(ndir):
        os.makedirs(ndir)
        print("New directory created")
        sc.api_call(
         "chat.postMessage",
          channel="#newgpfsdir",
          text=msg
         )
    else:
        print(ndir + " already exists!")
        sc.api_call(
         "chat.postMessage",
          channel="#newgpfsdir",
          text=emsg
         )
    
    # set permissions
    shutil.chown(ndir, user=owner, group=group)

createdir()

