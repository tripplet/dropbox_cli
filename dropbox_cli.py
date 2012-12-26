#!/usr/bin/python
# -*- coding: utf-8 -*-

# system imports
from __future__ import with_statement
from optparse import OptionParser
from datetime import date, datetime, timedelta
import readline # allows use of arrow keys in raw_input()
import ConfigParser, os, sys, io, json

# local imports
from dropbox import client, rest, session

# constants
CONFIG_NAME  = 'config.ini'

# global variables
account = ''
directory = '/'


# Main function
def main():
  global account

  if len(sys.argv) == 2:
    account = createDropboxClientForUser(sys.argv[1])

  printHelp()

  # endless command loop
  while True:
    try:
      command = raw_input('[' + directory + ']$ ')
    except KeyboardInterrupt, e:
      print
      exit()

    parseCommand(command)




def parseCommand(command):
  global account

  if command == 'help':
    printHelp()

  elif command == 'exit' or command == 'quit':
    exit()

  elif command == 'status':
    printStatus()

  elif command == 'listuser':
    listUsers()

  elif command == 'pwd':
    print directory

  elif command == 'ls':
    printDirectoryListing()

  elif command == 'll':
    printDirectoryListing(False)

  elif command.find('user ') == 0:
    account = createDropboxClientForUser(command[5:])

  elif command.find('cd ') == 0 or command == 'cd':
    changeDirectory(command[3:])

  elif command.find('rm ') == 0:
    deleteFile(command[3:])

  else:
    print 'Unknown command'

def deleteFile(file_path):
  account.file_delete(os.path.join(directory, file_path))

def moveFile(from_path, to_path):
  account.file_move(os.path.join(directory, from_path), os.path.join(directory, to_path))

def changeDirectory(new_dir):
  global directory

  if len(new_dir) == 0:
    directory = '/'

  if new_dir == '/':
    directory = new_dir
  else:
    if directory[-1:] != '/':
      directory = directory + '/'

    directory = directory + new_dir

def printDirectoryListing(short_list = True):
  file_list = account.metadata(directory)['contents']

  if short_list:
    for file_entry in file_list:
      file_name = file_entry['path'][1:]

      if type(file_name) == unicode:
        print file_name.encode('utf-8') + ' ',
      else:
        print file_name + ' ',
    print
  else:
    for file_entry in file_list:
      printDictPretty(file_entry)
      print

def printStatus():
  if account == '':
    print 'No user selected'
  else:
    printDictPretty(account.account_info())

def printDictPretty(obj, level=0):
  trailing = ''

  for x in range(0,level):
    trailing = trailing + ' '

  for key in obj:
    if type(obj[key]) == dict:
      print key + ':'
      printDictPretty(obj[key], level + 2)

    else:
      print trailing + key + ':',

      if type(obj[key]) == unicode:
        print obj[key].encode('utf-8')
      else:
        print str(obj[key])


def listUsers():
  # read config data
  cfg = ConfigParser.ConfigParser()
  cfg.read(getScriptPath() + '/' + CONFIG_NAME)

  for user in cfg.sections():
    # skip non [user-...] sections
    if user[0:5] != 'user-':
      continue

    print user[5:] + ' ',

  print


def printHelp():
  print "available commands: help, exit, cd, ls, ll, pwd, rm, mv, put, get, status, user, listuser"


def getScriptPath():
  return os.path.split(os.path.realpath(__file__))[0]

def createDropboxClientForUser(user):
  # read config data + dropbox-apikeys
  cfg = ConfigParser.ConfigParser()
  cfg.read(getScriptPath() + '/' + CONFIG_NAME)

  user = 'user-' + user

  sess = session.DropboxSession(cfg.get(user, 'app_key'),
                                cfg.get(user, 'app_secret'),
                                cfg.get(user, 'access_type'))

  sess.set_token(cfg.get(user, 'oauth_access_token'), \
                 cfg.get(user, 'oauth_access_token_secret'))

  return client.DropboxClient(sess)



######################
# SCRIPT STARTS HERE #
######################

if (__name__ == '__main__'):
  main()