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
import sys
import site

from cmd2 import Cmd

try:
    from ConfigParser import SafeConfigParser
except (ImportError, ModuleNotFoundError):
    from configparser import SafeConfigParser

# from lxml import etree, objectify

try:
    from besapi import besapi
except ModuleNotFoundError:
    # add the module path
    site.addsitedir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from besapi import besapi
except ImportError:
    # this is for the case in which we are calling bescli from besapi
    import besapi


class BESCLInterface(Cmd):
    """BES (BigFix) command-line interface processor."""

    def __init__(self, **kwargs):
        Cmd.__init__(self, **kwargs)
        self.prompt = "BES> "

        self.BES_ROOT_SERVER = None
        self.BES_USER_NAME = None
        self.BES_PASSWORD = None
        self.bes_conn = None

        # self.do_conf(None)

    def do_get(self, line):
        """Perform get request to BigFix server using provided api endpoint argument"""
        robjs = line.split(".")

        if self.bes_conn:
            if len(robjs) > 1:
                b = self.bes_conn.get(robjs[0])
                # print objectify.ObjectPath(robjs[1:])
                if b:
                    print(eval("b()." + ".".join(robjs[1:])))
            else:
                output_item = self.bes_conn.get(line)
                # print(type(output_item))
                print(output_item)
        else:
            print("Not currently logged in. Type 'login'.")

    def do_conf(self, conf_file):
        """Attempt to load config info from file and login"""
        if conf_file:
            config_path = conf_file
        else:
            config_path = [
                "/etc/besapi.conf",
                os.path.expanduser("~/besapi.conf"),
                "besapi.conf",
            ]

        CONFPARSER = SafeConfigParser()
        CONFPARSER.read(config_path)

        if CONFPARSER:

            try:
                self.BES_ROOT_SERVER = CONFPARSER.get("besapi", "BES_ROOT_SERVER")
            except:
                self.BES_ROOT_SERVER = None

            try:
                self.BES_USER_NAME = CONFPARSER.get("besapi", "BES_USER_NAME")
            except:
                self.BES_USER_NAME = None

            try:
                self.BES_PASSWORD = CONFPARSER.get("besapi", "BES_PASSWORD")
            except:
                self.BES_PASSWORD = None

        if self.BES_USER_NAME and self.BES_PASSWORD and self.BES_ROOT_SERVER:
            self.bes_conn = besapi.BESConnection(
                self.BES_USER_NAME, self.BES_PASSWORD, self.BES_ROOT_SERVER
            )
            if self.bes_conn.login():
                print("Login Successful!")
        else:
            # if any missing in config file, do interactive login:
            self.do_login()

    def do_login(self, user=None):
        """Login to BigFix Server"""
        # python3 hack:
        if sys.version_info >= (3, 0):
            raw_input = input

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
            root_server = raw_input(
                "Root Server (ex. %s): " % "https://server.institution.edu:52311"
            )
            if root_server:
                self.BES_ROOT_SERVER = root_server
            else:
                self.BES_ROOT_SERVER = None

        if self.BES_USER_NAME and self.BES_ROOT_SERVER:
            self.bes_conn = besapi.BESConnection(user, getpass.getpass(), root_server)
            if self.bes_conn.login():
                print("Login Successful!")
            else:
                print("Login Failed!")
                self.bes_conn = None
        else:
            print("Login Error!")

    def do_logout(self, arg):
        """Logout and clear session"""
        if self.bes_conn:
            self.bes_conn.logout()
            self.bes_conn = None

    def do_debug(self, setting):
        """Enable or Disable Debug Mode"""
        print(bool(setting))
        self.debug = bool(setting)
        self.echo = bool(setting)
        self.quiet = bool(setting)
        self.timing = bool(setting)

    def do_clear(self, arg=None):
        """clear current config and logout"""
        if self.bes_conn:
            self.bes_conn.logout()
            self.bes_conn = None
        self.BES_ROOT_SERVER = None
        self.BES_USER_NAME = None
        self.BES_PASSWORD = None

    def do_ls(self, arg=None):
        """List the current settings and connection status"""
        print(
            "BES_ROOT_SERVER: " + (self.BES_ROOT_SERVER if self.BES_ROOT_SERVER else "")
        )
        print("  BES_USER_NAME: " + (self.BES_USER_NAME if self.BES_USER_NAME else ""))
        print(
            "Password Length: "
            + str(len(self.BES_PASSWORD if self.BES_PASSWORD else ""))
        )
        print("      Connected: " + str(bool(self.bes_conn)))

    def do_exit(self, arg=None):
        """Exit this application"""
        sys.exit(0)


def main():
    BESCLInterface().cmdloop()


if __name__ == "__main__":
    main()