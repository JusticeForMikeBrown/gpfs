#!/usr/bin/env python3.6

__author__ = 'quackmaster@protonmail.com'

import argparse
import pwd
import os
import sys
import subprocess
from slackclient import SlackClient

support = 'help@dev.null'

parser = argparse.ArgumentParser()
parser.add_argument('user', help='user for which quota shall be modified')
parser.add_argument('filesystem', help='gpfs filesystem where quota exists')
parser.add_argument('fileset', help='fileset that contains quota')
parser.add_argument('newquota', help='new user quota to set expressed in TB')
print("\nThis script allows authorized power users to " +
      "change user-level GPFS quotas within centrally-managed filesets.\n")
print("For assistance contact", __author__, "or", support + "." "\n")
args = parser.parse_args()

# global vars
user = sys.argv[1]
filesystem = sys.argv[2] + ':'
fileset = sys.argv[3] + ''
newquota = sys.argv[4]

# assign 500K inodes per every TB
try:
    calcf = int(newquota) * int('500000')
except (ValueError, TypeError):
    print("Error! \n \nYou must use integer for new quota value not a string,"
          + " such as '5TB,' or float like '1.5.'")
    sys.exit()

# get user who ran script using sudo
runas_user = os.environ['SUDO_USER']

# slack variables
#
# token thus this script must not be readable by normal users
# also do not send this variable into gitlab
# slack_token = os.environ["QUOTA_TOKEN"]

st1 = "token1"
st2 = "token2"
st = st1 + st2
sc = SlackClient(st)

# slack messages sent
msg1 = user + ' quota on ' + fileset + ' changed by ' + runas_user
msg2 = ' to ' + newquota + 'TB' + ' ' + str(calcf) + ' inodes'
msg = msg1 + msg2
emsg1 = user + ' quota on ' + fileset
emsg2 = ' NOT changed due error - please contact ' + support
emsg = emsg1 + emsg2

# list of power users and defined filesets where user quotas can be set
lab = ['user', 'fs1', 'fs2']

# only allow power user to select filesets defined in this script
# this will maybe not scale well


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
        open('/var/adm/ras/mmfs.log.latest', 'r')
    except IOError:
        print("You must run this script on a GPFS node!")
        sys.exit()


gpfs_node()


# ensure running this script as root / sudo / lab power user
def privs():

    if runas_user == lab[0]:
        print("Changing for", sys.argv[1], "on fileset",
              sys.argv[3] + " by " + newquota + "T""\n")
    elif os.getuid() == 0:
        print("Changing for user", sys.argv[1], "on fileset",
              sys.argv[3] + " by " + newquota + "T""\n")
    else:
        print("You must run with sudo!", "\n \n""Contact", support)
        sys.exit()


privs()

# ensure that user which gets new quota actually exists


def checkuser():
    try:
        pwd.getpwnam(user)
    # add new users below along with new elif
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

    cmd1 = mmset + filesystem + fileset + user_s
    cmd2 = user + block_s + block + files_s + files
    changequota_cmd = cmd1 + cmd2

    # change the quota
    changeq = subprocess.run(changequota_cmd, timeout=10, shell=True)

    # print whether quota was changed
    if changeq.returncode == 0:
        print("User quota changed")
        sc.api_call("chat.postMessage", channel="#quotachange", text=msg)
    else:
        print("User quota unchanged due to error")
        sc.api_call("chat.postMessage", channel="#quotachange", text=emsg)


change_quota()
