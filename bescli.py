#!/usr/bin/env python
#
# Copyright 2014 The Pennsylvania State University.
#
"""
bescli.py

Created by Matt Hansen (mah60@psu.edu) on 2014-07-21.

Simple command line interface for the BES (BigFix) REST API.
"""

import os
import argparse
import getpass

from cmd2 import Cmd
from ConfigParser import SafeConfigParser
#from lxml import etree, objectify

import besapi

class BESCLInterface(Cmd):
    """BES (BigFix) command-line interface processor."""
    
    def __init__(self, **kwargs):
        Cmd.__init__(self, **kwargs)
        self.prompt = 'BES> '
        #self.do_conf(None)
        
        self.BES_ROOT_SERVER = None
        self.BES_USER_NAME = None
        self.BES_PASSWORD = None
        self.bes_conn = None

    def do_get(self, line):
        robjs = line.split('.')
        
        if self.bes_conn:
            if len(robjs) > 1:
                b = self.bes_conn.get(robjs[0])
                #print objectify.ObjectPath(robjs[1:])
                print(eval("b()." + '.'.join(robjs[1:])))
            else:
                print(self.bes_conn.get(line))
        else:
            print("Not currently logged in. Type 'login'.")

    def do_conf(self, conf_file):
        if conf_file:
            config_path = conf_file
        else:
            config_path = ['/etc/besapi.conf',
                           os.path.expanduser('~/besapi.conf'),
                           'besapi.conf']

        CONFPARSER = SafeConfigParser()
        CONFPARSER.read(config_path)
        
        if CONFPARSER:
        
            self.BES_ROOT_SERVER = CONFPARSER.get('besapi', 'BES_ROOT_SERVER')
            self.BES_USER_NAME = CONFPARSER.get('besapi', 'BES_USER_NAME')
            self.BES_PASSWORD = CONFPARSER.get('besapi', 'BES_PASSWORD')

        if self.BES_USER_NAME and self.BES_PASSWORD and self.BES_ROOT_SERVER:
            self.bes_conn = besapi.BESConnection(self.BES_USER_NAME,
                                                 self.BES_PASSWORD,
                                                 self.BES_ROOT_SERVER)
            if self.bes_conn.login(): print("Login Successful!")
        else:
            print("Login Failed!")

    def do_login(self, user):
    
        if not user:
            if self.BES_USER_NAME:
                user = self.BES_USER_NAME
            else:
                user = raw_input("User [%s]: " % getpass.getuser())
                if not user:
                    user = getpass.getuser()
            
            self.BES_USER_NAME = user
    
        if self.BES_ROOT_SERVER:
            root_server = raw_input("Root Server [%s]: " % self.BES_ROOT_SERVER)
            if not root_server:
                root_server = self.BES_ROOT_SERVER
            
            self.BES_ROOT_SERVER = root_server
            
        else:
            root_server = raw_input("Root Server (ex. %s): " % 
                                    'https://server.institution.edu:52311')
            if root_server:
                self.BES_ROOT_SERVER = root_server
            else:
                self.BES_ROOT_SERVER = None

        if self.BES_USER_NAME and self.BES_ROOT_SERVER:
            self.bes_conn = besapi.BESConnection(user,
                                                getpass.getpass(),
                                                root_server)
            if self.bes_conn.login():            
                print("Login Successful!")
            else:
                print("Login Failed!")
                self.bes_conn = None
        else:
            print("Login Error!")
            
    def do_logout(self, arg):

        if self.bes_conn:
            self.bes_conn.logout()
            self.bes_conn = None

    def do_debug(self, setting):
        print(bool(setting))
        self.debug = bool(setting)
        self.echo = bool(setting)
        self.quiet = bool(setting)
        self.timing = bool(setting)

def main():
    BESCLInterface().cmdloop()


if __name__ == '__main__':
    main()
