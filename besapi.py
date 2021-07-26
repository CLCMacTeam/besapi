#!/usr/bin/env python
#
# Copyright 2014 The Pennsylvania State University.
#
"""
besapi.py

Created by Matt Hansen (mah60@psu.edu) on 2014-03-20.

Library for communicating with the BES (BigFix) REST API.
"""

import requests
from lxml import etree, objectify
from pkg_resources import resource_filename

class BESConnection():

    def __init__(self, username, password, rootserver, verify=False):

        self.session = requests.Session()
        self.session.auth = (username, password)
        self.rootserver = rootserver
        self.verify = verify

        if not self.login():
            self.get('login').request.raise_for_status()

    def url(self, path):
        if path.startswith(self.rootserver):
            url = path
        else:
            url = "%s/api/%s" % (self.rootserver, path)

        return url

    def get(self, path='help', **kwargs):
        return RESTResult(self.session.get(self.url(path),
                                           verify=self.verify,
                                           **kwargs))

    def post(self, path, data, **kwargs):

        return RESTResult(self.session.post(self.url(path),
                                            data=data,
                                            verify=self.verify,
                                            **kwargs))

    def put(self, path, data, **kwargs):

        return RESTResult(self.session.put(self.url(path),
                                           data=data,
                                           verify=self.verify,
                                           **kwargs))

    def delete(self, path, **kwargs):

        return RESTResult(self.session.delete(self.url(path),
                                              verify=self.verify,
                                              **kwargs))

    def login(self):
        return bool(self.get('login').request.status_code == 200)

    def logout(self):
        self.session.auth = None
        self.session.cookies.clear()
        self.session.close()

    __call__ = login

class RESTResult():

    def __init__(self, request):
        self.request = request
        self.text = request.text
        self._besxml = None
        self._besobj = None

        if ('content-type' in request.headers and
                request.headers['content-type'] == 'application/xml'):
            self.valid = True
        elif (type(request.text) is str and
              self.validate_xsd(request.text.encode('utf-8'))):
            self.valid = True
        else:
            if self.validate_xsd(request.text):
                self.valid = True
            else:
                self.valid = False

    def __str__(self):
        if self.valid:
            return self.besxml
        else:
            return self.text

    def __call__(self):
        return self.besobj

    @property
    def besxml(self):
        if self.valid and self._besxml is None:
            self._besxml = self.xmlparse_text(self.text)

        return self._besxml

    @property
    def besobj(self):
        if self.valid and self._besobj is None:
            self._besobj = self.objectify_text(self.text)

        return self._besobj

    def validate_xsd(self, doc):
        try:
            xmldoc = etree.fromstring(doc)
        except:
            return False

        for xsd in ['BES.xsd', 'BESAPI.xsd', 'BESActionSettings.xsd']:
            xmlschema_doc = etree.parse(
                resource_filename(__name__, "schemas/%s" % xsd)
            )
            xmlschema = etree.XMLSchema(xmlschema_doc)

            if xmlschema.validate(xmldoc):
                return True

        return False

    def xmlparse_text(self, text):

        if type(text) is str:
            root_xml = etree.fromstring(text.encode('utf-8'))
        else:
            root_xml = text

        return etree.tostring(root_xml, encoding='utf-8',
                              xml_declaration=True)

    def objectify_text(self, text):

        if type(text) is str:
            root_xml = text.encode('utf-8')
        else:
            root_xml = text

        return objectify.fromstring(root_xml)

def main():
    import bescli
    bescli.main()


if __name__ == '__main__':
    main()
