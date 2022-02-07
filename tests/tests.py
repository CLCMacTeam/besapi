#!/usr/bin/env python
"""
Test besapi
"""

import argparse
import os
import subprocess
import sys

# check for --test_pip arg
parser = argparse.ArgumentParser()
parser.add_argument(
    "--test_pip", help="to test package installed with pip", action="store_true"
)
args = parser.parse_args()

if not args.test_pip:
    # add module folder to import paths for testing local src
    sys.path.append(
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
    )
    # reverse the order so we make sure to get the local src module
    sys.path.reverse()

import besapi
import bescli


print("besapi version: " + str(besapi.__version__))

bigfix_cli = bescli.bescli.BESCLInterface()

# just make sure these don't throw errors:
bigfix_cli.do_ls()
bigfix_cli.do_clear()
bigfix_cli.do_ls()
bigfix_cli.do_logout()
bigfix_cli.do_error_count()
bigfix_cli.do_version()
bigfix_cli.do_conf()

# this should really only run if the config file is present:
if bigfix_cli.bes_conn:
    print(bigfix_cli.bes_conn.session_relevance_string("number of bes computers"))

    # set working directory to folder this file is in:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # set working directory to src folder in parent folder
    os.chdir("../src")

    # Test file upload: print(bigfix_cli.bes_conn.upload("./besapi/__init__.py", "test_file.txt"))

    if os.name == "nt":
        subprocess.run(
            'CMD /C python -m besapi ls clear ls conf "query number of bes computers" version error_count exit',
            check=True,
        )
