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
        # Assign BES Console Variables
        bes_file = self.env.get("bes_file")
        bes_customsite = self.env.get("bes_customsite")
        BES_ROOTSERVER = self.env.get("BES_ROOTSERVER")
        BES_USERNAME = self.env.get("BES_USERNAME")
        BES_PASSWORD = self.env.get("BES_PASSWORD")

        bes_title = self.env.get("bes_title")

        # Console Connection Strings
        authString = base64.encodestring('%s:%s' %
                                         (BES_USERNAME, BES_PASSWORD)).strip()
        url = BES_ROOTSERVER + "/tasks/custom/" + bes_customsite

        self.output("Searching: '%s' for %s" % (url, bes_title))

        searchRequest = self.send_api_request(url, authString)
        searchDom = minidom.parseString(searchRequest.read())

        dupeTasks = []
        for result in searchDom.getElementsByTagName('Task') or []:
            if (result.getElementsByTagName('Name')[0].firstChild.nodeValue ==
                    bes_title):

                dupeTasks.append(int(
                    result.getElementsByTagName('ID')[0].firstChild.nodeValue))

                self.output("Found:[%s] %s - %s    " % (
                    result.getElementsByTagName('ID')[0].firstChild.nodeValue,
                    result.getElementsByTagName('Name')[0].firstChild.nodeValue,
                    result.attributes['LastModified'].value))

        if not dupeTasks:

            self.output("Importing: '%s' to %s/tasks/custom/%s" %
                        (bes_file, BES_ROOTSERVER, bes_customsite))

            importRequest = self.send_api_request(url, authString, bes_file)

            # Read and parse Console return
            resultDom = minidom.parseString(importRequest.read())
            resultTask = resultDom.getElementsByTagName('Task') or []
            resultName = resultTask[-1].getElementsByTagName('Name')
            resultID = resultTask[-1].getElementsByTagName('ID')

            self.env['bes_id'] = resultID[-1].firstChild.nodeValue
            self.output("Result (%s): [%s] %s - %s    " % (
                importRequest.getcode(),
                resultID[-1].firstChild.nodeValue,
                resultName[-1].firstChild.nodeValue,
                resultTask[-1].attributes['LastModified'].value))
        else:
            self.output("Skipping Import: " + str(dupeTasks))
            self.env['bes_id'] = str(dupeTasks)

if __name__ == "__main__":
    processor = BESImporter()
    processor.execute_shell()
