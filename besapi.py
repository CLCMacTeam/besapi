#!/usr/bin/env python
#
# Copyright 2014 The Pennsylvania State University.
#
"""
besapi.py

Created by Matt Hansen (mah60@psu.edu) on 2014-03-20.

Library for communicating with the BES (BigFix) REST API.
"""
import urlparse

import requests
from lxml import etree, objectify

class BESConnection():
 
    def __init__(self, username, password, rootserver):
        
        self.rootserver = rootserver
        self.session = requests.Session()
        self.session.auth = (username, password)
        
    def get(self, path='help'):
        url = "%s/api/%s" % (self.rootserver, path)
        
        return self.session.get(url, verify=False)
        
    def getREST(self, path='help'):
        response = self.get(path)
        
        if ('content-type' in response.headers and 
            response.headers['content-type'] == 'application/xml'):
                return RESTResult(response.text)
    
    def login(self):
        return bool(self.get('login').status_code == 200)
        
    def logout(self):
        self.session.auth = None
        self.session.close()
        
    __call__ = login
        
class RESTResult():

    def __init__(self, response_text):
        self.bytearray = response_text
        self._result = None
        self._besobj = None
        
    def __str__(self):
        return self.result

    def __call__(self):
        return self.besobj

    @property        
    def result(self):
        if self._result is None:
            self._result = self.xmlparse_byte(self.bytearray)
               
        return self._result
    
    @property
    def besobj(self):
        if self._besobj is None:
            self._besobj = self.objectify_byte(self.bytearray)
        
        return self._besobj
    
    def schema(self):
        return self.besobj.tag
            
    def xmlparse_byte(self, byte_array):
        
        if type(byte_array) is unicode:
            root_xml = etree.fromstring(byte_array.encode('utf-8'))
        else:
            root_xml = byte_array
            
        return etree.tostring(root_xml)
        
    def objectify_byte(self, byte_array):
    
        if type(byte_array) is unicode:
            root_xml = byte_array.encode('utf-8')
        else:
            root_xml = byte_array
                
        return objectify.fromstring(root_xml)

def main():
    # Command Line Funtions
    pass

if __name__ == '__main__':
    main()