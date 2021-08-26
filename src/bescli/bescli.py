#!/usr/bin/env python
"""
bescli.py

Created by Matt Hansen (mah60@psu.edu) on 2014-07-21.

Simple command line interface for the BES (BigFix) REST API.
"""

import getpass
import os
import site
import sys

import requests.exceptions
from cmd2 import Cmd

try:
    from ConfigParser import SafeConfigParser
except (ImportError, ModuleNotFoundError):
    from configparser import SafeConfigParser

try:
    from besapi import besapi
except ModuleNotFoundError:
    # add the module path
    site.addsitedir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from besapi import besapi
except ImportError:
    # this is for the case in which we are calling bescli from besapi
    import besapi

from besapi import __version__


class BESCLInterface(Cmd):
    """BigFix command-line interface processor."""

    def __init__(self, **kwargs):
        Cmd.__init__(self, **kwargs)
        self.prompt = "BigFix> "

        self.num_errors = 0
        self.BES_ROOT_SERVER = None
        self.BES_USER_NAME = None
        self.BES_PASSWORD = None
        self.bes_conn = None
        # set default config file path
        self.conf_path = os.path.expanduser("~/.besapi.conf")
        self.CONFPARSER = SafeConfigParser()
        self.do_conf()

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
            self.pfeedback("Not currently logged in. Type 'login'.")

    def do_config(self, conf_file=None):
        """Attempt to load config info from file and login"""
        self.do_conf(conf_file)

    def do_loadconfig(self, conf_file=None):
        """Attempt to load config info from file and login"""
        self.do_conf(conf_file)

    def do_conf(self, conf_file=None):
        """Attempt to load config info from file and login"""
        config_path = [
            "/etc/besapi.conf",
            os.path.expanduser("~/besapi.conf"),
            os.path.expanduser("~/.besapi.conf"),
            "besapi.conf",
        ]
        if self.conf_path not in config_path:
            config_path.append(self.conf_path)
        # if conf_file specified, then only use that:
        if conf_file:
            config_path = [conf_file]

        found_config_files = self.CONFPARSER.read(config_path)
        if found_config_files:
            self.pfeedback(f" - Found Config File(s):\n{found_config_files}")
            if found_config_files[0] != self.conf_path:
                self.conf_path = found_config_files[0]

        if self.CONFPARSER:

            try:
                self.BES_ROOT_SERVER = self.CONFPARSER.get("besapi", "BES_ROOT_SERVER")
            except BaseException:
                self.BES_ROOT_SERVER = None

            try:
                self.BES_USER_NAME = self.CONFPARSER.get("besapi", "BES_USER_NAME")
            except BaseException:
                self.BES_USER_NAME = None

            try:
                self.BES_PASSWORD = self.CONFPARSER.get("besapi", "BES_PASSWORD")
            except BaseException:
                self.BES_PASSWORD = None

        if self.BES_USER_NAME and self.BES_PASSWORD and self.BES_ROOT_SERVER:
            self.pfeedback(" - all values loaded from config file - ")
            # self.do_ls()
            self.pfeedback(" - attempt login using config parameters - ")
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
            if not self.CONFPARSER.has_section("besapi"):
                self.CONFPARSER.add_section("besapi")
            self.CONFPARSER.set("besapi", "BES_USER_NAME", user)

        if self.BES_ROOT_SERVER:
            root_server = self.BES_ROOT_SERVER
            if not root_server:
                root_server = raw_input("Root Server [%s]: " % self.BES_ROOT_SERVER)

            self.BES_ROOT_SERVER = root_server

        else:
            root_server = raw_input(
                "Root Server (ex. %s): " % "https://server.institution.edu:52311"
            )
            if root_server:
                self.BES_ROOT_SERVER = root_server
                if not self.CONFPARSER.has_section("besapi"):
                    self.CONFPARSER.add_section("besapi")
                self.CONFPARSER.set("besapi", "BES_ROOT_SERVER", root_server)
            else:
                self.BES_ROOT_SERVER = None

        if len(self.BES_PASSWORD if self.BES_PASSWORD else "") < 1:
            self.BES_PASSWORD = getpass.getpass()
            if not self.CONFPARSER.has_section("besapi"):
                self.CONFPARSER.add_section("besapi")
            self.CONFPARSER.set("besapi", "BES_PASSWORD", self.BES_PASSWORD)

        if self.BES_USER_NAME and self.BES_ROOT_SERVER and self.BES_PASSWORD:
            try:
                self.bes_conn = besapi.BESConnection(
                    user, self.BES_PASSWORD, root_server
                )
                if self.bes_conn.login():
                    self.pfeedback("Login Successful!")
                else:
                    self.perror("Login Failed!")
                    # clear likely bad password
                    self.BES_PASSWORD = None
                    # clear failed connection
                    self.bes_conn = None
            except requests.exceptions.HTTPError as err:
                self.perror(err)
                self.num_errors += 1
                self.pfeedback("-- clearing likely bad password --")
                self.BES_PASSWORD = None
                # clear failed connection
                self.bes_conn = None
                self.do_ls()
                if self.debug:
                    # this will allow the stacktrace to be printed
                    raise
            except requests.exceptions.ConnectionError as err:
                self.perror(err)
                self.num_errors += 1
                self.pfeedback("-- clearing likely bad root server --")
                self.BES_ROOT_SERVER = None
                # clear failed connection
                self.bes_conn = None
                self.do_ls()
                if self.debug:
                    # this will allow the stacktrace to be printed
                    raise
        else:
            self.perror("Login Error!")

    def do_logout(self, arg):
        """Logout and clear session"""
        if self.bes_conn:
            self.bes_conn.logout()
            self.bes_conn = None
        self.pfeedback("Logout Complete!")

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
        if arg and "root" in arg.lower():
            self.pfeedback(" - clearing root server parameter -")
            self.BES_ROOT_SERVER = None
        if arg and "user" in arg.lower():
            self.pfeedback(" - clearing user parameter -")
            self.BES_USER_NAME = None
        if arg and "pass" in arg.lower():
            self.pfeedback(" - clearing password parameter -")
            self.BES_PASSWORD = None
        if not arg:
            self.pfeedback(" - clearing all parameters -")
            self.BES_ROOT_SERVER = None
            self.BES_USER_NAME = None
            self.BES_PASSWORD = None

    def do_saveconfig(self, arg=None):
        """save current config to file"""
        self.do_saveconf(arg)

    def do_saveconf(self, arg=None):
        """save current config to file"""
        if not self.bes_conn:
            self.do_login()
        if not self.bes_conn:
            print("Can't save config without working login")
        else:
            conf_file_path = self.conf_path
            self.pfeedback(f"Saving Config File to: {conf_file_path}")
            with open(conf_file_path, "w") as configfile:
                self.CONFPARSER.write(configfile)

    def do_showconfig(self, arg=None):
        """List the current settings and connection status"""
        self.do_ls(arg)

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
        print("Config File Path: " + self.conf_path)

    def do_error_count(self, arg=None):
        """Output the number of errors"""
        self.poutput(self.num_errors)

    def do_exit(self, arg=None):
        """Exit this application"""
        self.exit_code = self.num_errors
        # no matter what I try I can't get anything but exit code 0 on windows
        return self.do_quit("")

    def do_query(self, statement):
        """Get Session Relevance Results"""
        if not self.bes_conn:
            self.do_login()
        if not self.bes_conn:
            self.poutput("ERROR: can't query without login")
        else:
            if statement.raw:
                # get everything after `query `
                rel_text = statement.raw.split(" ", 1)[1]
                self.poutput("Q: " + rel_text)
                rel_result = self.bes_conn.session_relevance_string(rel_text)
                self.poutput(rel_result)

    def do_version(self, statement):
        """output version of besapi"""
        print(__version__)


def main():
    """Run the command loop if invoked"""
    BESCLInterface().cmdloop()


if __name__ == "__main__":
    main()
