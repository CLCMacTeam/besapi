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
from xml.dom import minidom

from autopkglib import Processor, ProcessorError

__all__ = ["BESUploader"]

class BESUploader(Processor):
    description = "Uploads a file to the BES Console. Requires Master Operator Rights!"
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
        request = urllib2.Request(api_url)

        request.add_header("Authorization", "Basic %s" % auth_string)
        request.add_header("Content-Type", "application/xml")

        # Read bes_file contents and add to request
        if bes_file:
            bes_data = open(bes_file).read()
            request.add_data(bes_data)
            request.add_header("Content-Disposition", 'attachment; filename="%s"' % 
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
        # Assign Console Variables
        bes_uploadpath = self.env.get("bes_uploadpath")
        BES_ROOTSERVER = self.env.get("BES_ROOTSERVER").encode('ascii')
        BES_USERNAME = self.env.get("BES_USERNAME")
        BES_PASSWORD = self.env.get("BES_PASSWORD")
        
        self.output("Uploading: %s to %s" % (bes_uploadpath, 
                                             BES_ROOTSERVER + '/upload'))
        
        # Console Connection Strings
        authString = base64.encodestring('%s:%s' %
                                         (BES_USERNAME, BES_PASSWORD)).strip()
        # Send Request
        uploadRequest = self.send_api_request(BES_ROOTSERVER + "/upload",
                                              authString, bes_uploadpath)
        
        #Read and Parse Console Return
        resultDom = minidom.parseString(uploadRequest.read())
        resultUpload = resultDom.getElementsByTagName('FileUpload') or []
        resultName = resultUpload[-1].getElementsByTagName('Name')
        resultURL = resultUpload[-1].getElementsByTagName('URL')
        resultSize = resultUpload[-1].getElementsByTagName('Size')
        resultSHA1 = resultUpload[-1].getElementsByTagName('SHA1')
        
        # Set Output Variables
        self.env['bes_uploadname'] = resultName[-1].firstChild.nodeValue
        self.env['bes_uploadurl'] = resultURL[-1].firstChild.nodeValue
        self.env['bes_uploadsize'] = resultSize[-1].firstChild.nodeValue
        self.env['bes_uploadsha1'] = resultSHA1[-1].firstChild.nodeValue

        self.env['bes_prefetch'] = "prefetch %s sha1:%s size:%s %s" % (
                                   self.env.get("bes_uploadname"),
                                   self.env.get("bes_uploadsha1"),
                                   self.env.get("bes_uploadsize"),
                                   self.env.get("bes_uploadurl"),
        )
        
        self.output("Result (%s): %s    " % (
            uploadRequest.getcode(),
            resultUpload[-1].attributes['Resource'].value))

if __name__ == "__main__":
    processor = BESUploader()
    processor.execute_shell()