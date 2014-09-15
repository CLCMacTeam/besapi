#!/usr/bin/python
# encoding: utf-8
#
# Copyright 2013 The Pennsylvania State University.
#
"""
BESUploader.py

Created by Matt Hansen (mah60@psu.edu) on 2013-11-06.

AutoPkg Processor for uploading files using the BigFix REST API
"""

import os
import urllib2
import base64
import sys
from xml.dom import minidom

from autopkglib import Processor, ProcessorError

__all__ = ["BESUploader"]

class BESUploader(Processor):
    """AutoPkg Processor for uploading files using the BigFix REST API"""
    description = "Uploads a file to the BES Console. Requires Master Operator."
    input_variables = {
        "bes_uploadpath": {
            "required": True,
            "description":
                "Path to the file to import into the console."
        },
        "BES_ROOTSERVER": {
            "required": True,
            "description":
                "URL to BES root server. e.g https://bes.domain.tld:52311/api"
        },
        "BES_USERNAME": {
            "required": True,
            "description":
                "BES console username with upload permissions."
        },
        "BES_PASSWORD": {
            "required": True,
            "description":
                "BES console password for bes_username."
        },
    }
    output_variables = {
        "bes_uploadname": {
            "description":
                "The resulting name of the BES console upload."
        },
        "bes_uploadurl": {
            "description":
                "The resulting url of the BES console upload."
        },
        "bes_uploadsha1": {
            "description":
                "The resulting sha1 of the BES console upload."
        },
        "bes_uploadsize": {
            "description":
                "The resulting size of the BES console upload."
        },
        "bes_prefetch": {
            "description":
                "The compiled prefetch command for the uploaded file."
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
            request.add_header("Content-Disposition",
                               'attachment; filename="%s"' %
                               os.path.basename(bes_file))

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
        """BESUploader Main Method"""
        # Assign Console Variables
        bes_uploadpath = self.env.get("bes_uploadpath")
        BES_ROOTSERVER = self.env.get("BES_ROOTSERVER").encode('ascii')
        BES_USERNAME = self.env.get("BES_USERNAME")
        BES_PASSWORD = self.env.get("BES_PASSWORD")

        self.output("Uploading: %s to %s" % (bes_uploadpath,
                                             BES_ROOTSERVER + '/upload'))

        # Console Connection Strings
        auth_string = base64.encodestring('%s:%s' %
                                          (BES_USERNAME, BES_PASSWORD)).strip()
        # Send Request
        upload_request = self.send_api_request(BES_ROOTSERVER + "/upload",
                                               auth_string, bes_uploadpath)

        #Read and Parse Console Return
        result_dom = minidom.parseString(upload_request.read())
        result_upload = result_dom.getElementsByTagName('FileUpload') or []
        result_name = result_upload[-1].getElementsByTagName('Name')
        result_url = result_upload[-1].getElementsByTagName('URL')
        result_size = result_upload[-1].getElementsByTagName('Size')
        result_sha1 = result_upload[-1].getElementsByTagName('SHA1')

        # Set Output Variables
        self.env['bes_uploadname'] = result_name[-1].firstChild.nodeValue
        self.env['bes_uploadurl'] = result_url[-1].firstChild.nodeValue
        self.env['bes_uploadsize'] = result_size[-1].firstChild.nodeValue
        self.env['bes_uploadsha1'] = result_sha1[-1].firstChild.nodeValue

        self.env['bes_prefetch'] = (
            "prefetch %s sha1:%s size:%s %s" % (
                self.env.get("bes_uploadname"),
                self.env.get("bes_uploadsha1"),
                self.env.get("bes_uploadsize"),
                self.env.get("bes_uploadurl"),
            )
        )

        self.output("Result (%s): %s    " % (
            upload_request.getcode(),
            result_upload[-1].attributes['Resource'].value))

if __name__ == "__main__":
    processor = BESUploader()
    processor.execute_shell()
