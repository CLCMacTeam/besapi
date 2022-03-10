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

print("besapi version: " + str(besapi.__version__))

# test site_path string validation
assert "master" in besapi.besapi.BESConnection.validate_site_path("", "master", False)
assert "custom/" in besapi.besapi.BESConnection.validate_site_path(
    "", "custom/Example", False
)
assert "operator/" in besapi.besapi.BESConnection.validate_site_path(
    "", "operator/Example", False
)

# start failing tests:
raised_errors = 0

# failing test:
try:
    besapi.besapi.BESConnection.validate_site_path("", "bad/Example", False)
except ValueError:
    raised_errors += 1

# failing test:
try:
    besapi.besapi.BESConnection.validate_site_path("", "bad/master", False)
except ValueError:
    raised_errors += 1

# failing test:
try:
    besapi.besapi.BESConnection.validate_site_path("", "", False, True)
except ValueError:
    raised_errors += 1

# failing test:
try:
    besapi.besapi.BESConnection.validate_site_path("", None, False, True)
except ValueError:
    raised_errors += 1

assert raised_errors == 4
# end failing tests


class RequestResult(object):
    text = "this is just a test"
    headers = []


request_result = RequestResult()
rest_result = besapi.besapi.RESTResult(request_result)

print(rest_result.besdict)
print(rest_result.besjson)
assert b"<BES>Example</BES>" in rest_result.xmlparse_text("<BES>Example</BES>")

assert rest_result.text == "this is just a test"

import bescli

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
    # session relevance tests require functioning web reports server
    print(bigfix_cli.bes_conn.session_relevance_string("number of bes computers"))
    assert (
        "test session relevance string result"
        in bigfix_cli.bes_conn.session_relevance_string(
            '"test session relevance string result"'
        )
    )
    bigfix_cli.do_set_current_site("master")

    # set working directory to folder this file is in:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # set working directory to src folder in parent folder
    os.chdir("../src")

    # Test file upload:
    print(bigfix_cli.bes_conn.upload("./besapi/__init__.py", "test_besapi_upload.txt"))

    if os.name == "nt":
        subprocess.run(
            'CMD /C python -m besapi ls clear ls conf "query number of bes computers" version error_count exit',
            check=True,
        )
