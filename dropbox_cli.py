#!/usr/bin/python
# -*- coding: utf-8 -*-

# system imports
from __future__ import with_statement
from optparse import OptionParser
from datetime import date, datetime, timedelta
import readline # allows use of arrow keys in raw_input()
import ConfigParser, json
import os, sys, io

# local imports
from dropbox import client, rest, session

# constants
CONFIG_NAME  = 'config.ini'
CHUNK_SIZE = 1024 * 1024 # 1mb

# global variables
account = ''
remote_directory = '/'
local_directory = ''
user = ''
copy_refs = []


# Main function
def main():
  global account
  global user
  global local_directory

  local_directory = getScriptPath()

  if len(sys.argv) == 2:
    try:
      account = createDropboxClientForUser(sys.argv[1])
      user = sys.argv[1]
    except:
      pass

  printHelp()

  # endless command loop
  while True:
    try:
      command = raw_input(user + '[' + remote_directory + ']$ ')
    except KeyboardInterrupt, e:
      print
      exit()

    parseCommand(command)


def parseCommand(command):
  global account
  global remote_directory
  global user

  if command == '':
    pass

  elif command == 'help':
    printHelp()

  elif command == 'exit' or command == 'quit':
    exit()

  elif command == 'status':
    printStatus()

  elif command == 'listuser':
    listUsers()

  elif command == 'pwd':
    print remote_directory

  elif command == 'lpwd':
    print local_directory

  elif command == 'ls':
    printRemoteDirectoryListing()

  elif command == 'll':
    printRemoteDirectoryListing(False)

  elif command == 'lls':
    printLocalDirectoryListing()

  elif command.find('user ') == 0:
    try:
      account = createDropboxClientForUser(command[5:])
      remote_directory = '/'
      user = command[5:]

    except:
      print 'Error user not valid'

  elif command.find('cd ') == 0 or command == 'cd':
    changeRemoteDirectory(command[3:])

  elif command.find('lcd ') == 0 or command == 'lcd':
    changeLocalDirectory(command[4:])

  elif command.find('rm ') == 0:
    deleteFile(command[3:])

  elif command.find('put ') == 0:
    uploadFile(command[4:])

  elif command.find('get ') == 0:
    downloadFile(command[4:])

  elif command.find('copy ') == 0:
    generateCopyRef(command[5:])

  elif command.find('paste ') == 0:
    pasteCopyRef(command[6:7], command[8:])

  elif command.find('mkdir ') == 0:
    makeRemoteDirectory(command[6:])

  else:
    print 'Unknown command'


def generateCopyRef(filename):
  global copy_refs

  if not checkConnection():
    return

  try:
     ref = account.create_copy_ref(os.path.join(remote_directory, filename))['copy_ref']
     copy_refs.append(ref)

     print 'Saved in clipboard pos [' + str(len(copy_refs) - 1) + ']'
  except Exception, e:
    print 'Error: ' + str(e)


def pasteCopyRef(number, filename):
  if not checkConnection():
    return

  try:
     account.add_copy_ref(copy_refs[int(number)], os.path.join(remote_directory, filename))

  except Exception, e:
    print 'Error: ' + str(e)


def makeRemoteDirectory(dir_name):
  if not checkConnection():
    return

  try:
    account.file_create_folder(os.path.join(remote_directory, dir_name))
  except Exception, e:
    print 'Error: ' + str(e)


def downloadFile(filename):
  if not checkConnection():
    return

  try:
    stream_handle = account.get_file(os.path.join(remote_directory, filename))

    sys.stdout.write('Downloading')
    sys.stdout.flush()

    # download file
    with open(os.path.join(local_directory, filename), 'wb') as fp:
      while True:
        data = stream_handle.read(CHUNK_SIZE)

        sys.stdout.write(".")
        sys.stdout.flush()

        if not data:
          break

        fp.write(data)
    sys.stdout.write('\nDone\n')
  except Exception, e:
    print 'Error: ' + str(e)


def uploadFile(filename):
  if not checkConnection():
    return

  local_file_path = os.path.join(local_directory, filename)
  remote_file_path = os.path.join(remote_directory, filename)
  file_size = os.path.getsize(local_file_path)

  try:
    with open(local_file_path, 'rb') as fp:
      uploader = account.get_chunked_uploader(fp, file_size)
      print 'Uploading ...'
      uploader.upload_chunked(CHUNK_SIZE)
      uploader.finish(remote_file_path)
  except Exception, e:
    print 'Error: ' + str(e)



def deleteFile(file_path):
  if not checkConnection():
    return

  try:
    account.file_delete(os.path.join(remote_directory, file_path))
  except Exception, e:
    print 'Error: ' + str(e)


def moveFile(from_path, to_path):
  if not checkConnection():
    return

  try:
    account.file_move(os.path.join(remote_directory, from_path), os.path.join(remote_directory, to_path))
  except Exception, e:
    print 'Error: ' + str(e)

def changeLocalDirectory(new_dir):
  global local_directory

  if len(new_dir) == 0:
    new_local_directory = getScriptPath()
  else:
    if new_dir[0] == '/':
      new_local_directory = new_dir
    elif new_dir == '..':
      new_local_directory = os.path.dirname(local_directory)
    else:
      if local_directory[-1:] != '/':
        new_local_directory = local_directory + '/'

      new_local_directory = new_local_directory + new_dir

  if os.path.exists(new_local_directory):
    local_directory = new_local_directory
  else:
    print 'No such directory'


def changeRemoteDirectory(new_dir):
  global remote_directory

  if len(new_dir) == 0:
    remote_directory = '/'
  else:
    if new_dir[0] == '/':
      remote_directory = new_dir
    elif new_dir == '..':
      remote_directory = os.path.dirname(remote_directory)
    else:
      if remote_directory[-1:] != '/':
        remote_directory = remote_directory + '/'

      remote_directory = remote_directory + new_dir

def getTerminalSize():
    import os
    env = os.environ
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct, os
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,
        '1234'))
        except:
            return
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        cr = (env.get('LINES', 25), env.get('COLUMNS', 80))

        ### Use get(key[, default]) instead of a try/catch
        #try:
        #    cr = (env['LINES'], env['COLUMNS'])
        #except:
        #    cr = (25, 80)
    return int(cr[1]), int(cr[0])

def checkConnection():
  if account == '':
    print 'No user selected'
    return False
  else:
    return True

def printInColumns(entries):
  if len(entries) == 0:
    return

  col_width = max(len(word) for word in entries) + 3  # padding

  if sys.stdout.isatty():
    (tty_width, tty_height) = getTerminalSize()
    columns = tty_width / col_width
  else:
    columns = 6

  row_count = 0

  for entry in entries:
    sys.stdout.write(entry.ljust(col_width).encode('utf-8'))
    row_count = row_count + 1

    if row_count == columns:
      row_count = 0
      print

  if row_count !=0:
    print

def printLocalDirectoryListing():
  file_entries = os.listdir(local_directory)
  entries = []

  for entry in file_entries:
    if os.path.isdir(os.path.join(local_directory, entry)):
      entries.append(entry + '/')
    else:
      entries.append(entry)

  printInColumns(entries)



def printRemoteDirectoryListing(short_list = True):
  if not checkConnection():
    return

  try:
    file_list = account.metadata(remote_directory)['contents']
  except Exception, e:
    print 'Error: ' + str(e)
    return

  if short_list:
    entries = []

    for entry in file_list:
      if entry['is_dir']:
        entries.append(os.path.basename(entry['path'][1:]) + '/')
      else:
        entries.append(os.path.basename(entry['path'][1:]))

    printInColumns(entries)

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
  trailing = ' ' * level

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
  print "available commands: help, exit, cd, lcd, mkdir, lpwd, ls, ll, pwd, rm, mv, put, get, status, user, listuser, paste, copy"


def getScriptPath():
  return os.path.split(os.path.realpath(__file__))[0]


def createDropboxClientForUser(new_user):
  # read config data + dropbox-apikeys
  cfg = ConfigParser.ConfigParser()
  cfg.read(getScriptPath() + '/' + CONFIG_NAME)

  cfg_user = 'user-' + new_user

  sess = session.DropboxSession(cfg.get(cfg_user, 'app_key'),
                                cfg.get(cfg_user, 'app_secret'),
                                cfg.get(cfg_user, 'access_type'))

  sess.set_token(cfg.get(cfg_user, 'oauth_access_token'), \
                 cfg.get(cfg_user, 'oauth_access_token_secret'))

  return client.DropboxClient(sess)



######################
# SCRIPT STARTS HERE #
######################

if (__name__ == '__main__'):
  main()