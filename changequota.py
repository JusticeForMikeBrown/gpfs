#!/usr/bin/env python3.6

__author__ = 'quackmaster@protonmail.com'

import argparse
import pwd
import os
import sys
import subprocess
from slackclient import SlackClient

support = 'helpdesk@dev.null'

parser = argparse.ArgumentParser()
parser.add_argument('user',  help='user for which quota shall be modified')
parser.add_argument('filesystem',  help='gpfs filesystem where quota exists')
parser.add_argument('fileset',  help='fileset that contains quota')
parser.add_argument('newquota',  help='new user quota to set expressed in TB')
print("\nThis script allows authorized power users to change user-level GPFS quotas within centrally-managed filesets.\n")
print("For assistance contact", __author__, "or" , support +"." "\n")
args = parser.parse_args()

# global vars
user = sys.argv[1]
filesystem = sys.argv[2] + ':'
fileset = sys.argv[3] + ''
newquota  = sys.argv[4]    

# must use int for newquota value 
def useint():

    if isinstance(newquota, int):
       print()
    else:
        print("Error! \n \nYou must use integer for new quota value not a string, such as '5TB,' or float like '1.5.'")
        sys.exit()

useint()

# assign 500K inodes per every TB
calcf = int(newquota) * int('500000')

# get user who ran script using sudo
runas_user = os.environ['SUDO_USER']

# slack variables
#
#token thus this script must not be readable by normal users 
# also do not send this variable into gitlab
# alternatively
# one can use the below with bash variable
#slack_token = os.environ["QUOTA_TOKEN"]

slack_token = "oauth_blah"
sc = SlackClient(slack_token)

# slack messages sent 
msg = user + ' quota on ' + fileset + ' changed by ' + runas_user + ' to ' + newquota + 'TB' + ' ' + str(calcf) + ' inodes'
emsg = user + ' quota on ' + fileset + ' NOT changed due error - please contact ' + support

# list of power users and defined filesets where user quotas can be set
lab = [ 'poweruser', 'fileset1' , 'fileset2' ]

# only allow power user to select filesets defined in this script
# this will maybe not scale well as number of labs > 1
def sanitize():

    if fileset == lab[1]:
        print("Valid filset chosen\n")
    elif fileset == lab[2]:
        print("Valid filset chosen\n")
    else:
        print("You must choose a valid fileset.  Exiting...")
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

# ensure running this script as root / sudo / lab power user
def privs():

    if runas_user == lab[0]:
        print("Changing quota for user", sys.argv[1], "on fileset", sys.argv[3] + " by " + newquota + "T""\n")
    elif os.getuid() == 0:
        print("Changing quota for user", sys.argv[1], "on fileset", sys.argv[3] + " by " + newquota + "T""\n")
    else:
        print("You must run with sudo!", "\n \n""Contact", support, "for assistance.")
        sys.exit()
privs()

# ensure that user which gets new quota actually exists
def checkuser():
    try:
        pwd.getpwnam(user)
    except KeyError:
        print("User", user, "does not exist.")
        sys.exit()

checkuser()

def change_quota():

    user = sys.argv[1]
    mmset = '/usr/lpp/mmfs/bin/mmsetquota '
    user_s = ' --user '
    block_s = ' --block '
    files_s = ' --files '
    block = newquota + 'T' + ':' + newquota + 'T'
    files = str(calcf) + ':' + str(calcf)

    cquota_command = mmset + filesystem + fileset + user_s + user + block_s + block + files_s + files

    # change the quota
    changeq = subprocess.run(cquota_command, timeout=10, shell=True)

    # print whether quota was changed
    if changeq.returncode == 0:
        print("User quota changed")
        sc.api_call(
         "chat.postMessage",
          channel="#quotachange",
          text=msg
         )
    else:
        print("User quota unchanged due to error")
        sc.api_call(
         "chat.postMessage",
          channel="#quotachange",
          text=emsg
         )

change_quota()

