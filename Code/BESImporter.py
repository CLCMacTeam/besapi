#!/usr/bin/python
# encoding: utf-8
#
# Copyright 2013 The Pennsylvania State University.
#
"""
BESImporter.py

Created by Matt Hansen (mah60@psu.edu) on 2013-11-04.

AutoPkg Processor for importing tasks using the BigFix RESTAPI
"""

import urllib2
import base64
import sys
from xml.dom import minidom

from autopkglib import Processor, ProcessorError

__all__ = ["BESImporter"]

class BESImporter(Processor):
    """AutoPkg Processor for importing tasks using the BigFix RESTAPI"""
    description = "Generates BigFix XML to install application."
    input_variables = {
        "bes_file": {
            "required": True,
            "description":
                "Path to BES XML file for console import."
        },
        "bes_customsite": {
            "required": True,
            "description":
                "BES console custom site for generated content."
        },
        "BES_ROOTSERVER": {
            "required": True,
            "description":
                "URL to BES root server. e.g https://bes.domain.tld:52311/api"
        },
        "BES_USERNAME": {
            "required": True,
            "description":
                "Console username with write permissions to BES_CUSTOMSITE."
        },
        "BES_PASSWORD": {
            "required": True,
            "description":
                "Console password for BES_USERNAME."
        },
    }
    output_variables = {
        "bes_id": {
            "description":
                "The resulting ID of the BES console import."
        },
    }
    __doc__ = description

    def send_api_request(self, api_url, auth_string, bes_file=None):
        """Send generic BES API request"""
        request = urllib2.Request(api_url)

        request.add_header("Authorization", "Basic %s" % auth_string)
        request.add_header("Content-Type", "application/xml")

        # Read bes_file contents and add to request
        if bes_file:
            bes_data = open(bes_file).read()
            request.add_data(bes_data)

        # Request POST to Console API
        try:
            return urllib2.urlopen(request)

        except urllib2.HTTPError, error:
            self.output("HTTPError: [%s] %s" % (error.code, error.read()))
            sys.exit(1)
        except urllib2.URLError, error:
            self.output("URLError: %s" % (error.args))
            sys.exit(1)

    def main(self):
        """BESImporter Main Method"""
        # Assign BES Console Variables
        bes_file = self.env.get("bes_file")
        bes_customsite = self.env.get("bes_customsite")
        BES_ROOTSERVER = self.env.get("BES_ROOTSERVER")
        BES_USERNAME = self.env.get("BES_USERNAME")
        BES_PASSWORD = self.env.get("BES_PASSWORD")

        bes_title = self.env.get("bes_title")

        # Console Connection Strings
        auth_string = base64.encodestring('%s:%s' %
                                          (BES_USERNAME, BES_PASSWORD)).strip()

        url = BES_ROOTSERVER + "/tasks/custom/" + bes_customsite

        self.output("Searching: '%s' for %s" % (url, bes_title))

        search_request = self.send_api_request(url, auth_string)
        search_dom = minidom.parseString(search_request.read())

        dupe_tasks = []
        for result in search_dom.getElementsByTagName('Task') or []:
            if (result.getElementsByTagName('Name')[0].firstChild.nodeValue ==
                    bes_title):

                dupe_tasks.append(int(
                    result.getElementsByTagName('ID')[0].firstChild.nodeValue))

                self.output("Found:[%s] %s - %s    " % (
                    result.getElementsByTagName('ID')[0].firstChild.nodeValue,
                    result.getElementsByTagName('Name')[0].firstChild.nodeValue,
                    result.attributes['LastModified'].value))

        if not dupe_tasks:

            self.output("Importing: '%s' to %s/tasks/custom/%s" %
                        (bes_file, BES_ROOTSERVER, bes_customsite))

            import_request = self.send_api_request(url, auth_string, bes_file)

            # Read and parse Console return
            result_dom = minidom.parseString(import_request.read())
            result_task = result_dom.getElementsByTagName('Task') or []
            result_name = result_task[-1].getElementsByTagName('Name')
            result_id = result_task[-1].getElementsByTagName('ID')

            self.env['bes_id'] = result_id[-1].firstChild.nodeValue
            self.output("Result (%s): [%s] %s - %s    " % (
                import_request.getcode(),
                result_id[-1].firstChild.nodeValue,
                result_name[-1].firstChild.nodeValue,
                result_task[-1].attributes['LastModified'].value))
        else:
            self.output("Skipping Import: " + str(dupe_tasks))
            self.env['bes_id'] = str(dupe_tasks)

if __name__ == "__main__":
    processor = BESImporter()
    processor.execute_shell()
