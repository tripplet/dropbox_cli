#!/usr/bin/python
# -*- coding: utf-8 -*-

from dropbox import client, rest, session

# Get your app key and secret from the Dropbox developer website
APP_KEY = ''
APP_SECRET = ''

# ACCESS_TYPE should be 'dropbox' or 'app_folder' as configured for your app
ACCESS_TYPE = 'app_folder'

sess = session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)
request_token = sess.obtain_request_token()
url = sess.build_authorize_url(request_token)

# Make the user sign in and authorize this token
print "url: ", url
print "Please visit this website and press the 'Allow' button, then hit 'Enter' here."
raw_input()

print "requesting token ..."
# This will fail if the user didn't visit the above URL and hit 'Allow'
access_token = sess.obtain_access_token(request_token)

client = client.DropboxClient(sess)

print ""
print "linked account: ", client.account_info()
print ""
print "access_token: key=", str(access_token.key), "  secret=", str(access_token.secret)