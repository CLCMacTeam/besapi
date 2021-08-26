#!/usr/bin/env python
#
# Copyright 2014 The Pennsylvania State University.
#
"""
besapi.py

Created by Matt Hansen (mah60@psu.edu) on 2014-03-20.
Enhancements by James Stewart since 2021

Library for communicating with the BES (BigFix) REST API.
"""

import os.path
import site
import urllib.parse

import requests
from lxml import etree, objectify
from pkg_resources import resource_filename


class BESConnection:
    """BigFix RESTAPI connection abstraction class"""

    def __init__(self, username, password, rootserver, verify=False):

        if not verify:
            # disable SSL warnings
            requests.packages.urllib3.disable_warnings()  # pylint: disable=no-member

        self.session = requests.Session()
        self.session.auth = (username, password)

        # if not provided, add on https://
        if not rootserver.startswith("http"):
            rootserver = "https://" + rootserver
        # if port not provided, add on the default :52311
        if not rootserver.count(":") == 2:
            rootserver = rootserver + ":52311"

        self.rootserver = rootserver
        self.verify = verify

        if not self.login():
            self.get("login").request.raise_for_status()

    def url(self, path):
        """get absolute url"""
        if path.startswith(self.rootserver):
            url = path
        else:
            url = "%s/api/%s" % (self.rootserver, path)

        return url

    def get(self, path="help", **kwargs):
        """HTTP GET request"""
        return RESTResult(
            self.session.get(self.url(path), verify=self.verify, **kwargs)
        )

    def post(self, path, data, **kwargs):
        """HTTP POST request"""
        return RESTResult(
            self.session.post(self.url(path), data=data, verify=self.verify, **kwargs)
        )

    def put(self, path, data, **kwargs):
        """HTTP PUT request"""
        return RESTResult(
            self.session.put(self.url(path), data=data, verify=self.verify, **kwargs)
        )

    def delete(self, path, **kwargs):
        """HTTP DELETE request"""
        return RESTResult(
            self.session.delete(self.url(path), verify=self.verify, **kwargs)
        )

    def session_relevance_xml(self, relevance, **kwargs):
        """Get Session Relevance Results XML"""
        return RESTResult(
            self.session.post(
                self.url("query"),
                data=f"relevance={urllib.parse.quote(relevance, safe=':+')}",
                verify=self.verify,
                **kwargs,
            )
        )

    def session_relevance_array(self, relevance, **kwargs):
        """Get Session Relevance Results array"""
        rel_result = self.session_relevance_xml(relevance, **kwargs)
        # print(rel_result)
        result = []
        try:
            for item in rel_result.objectify_text(rel_result.text).Query.Result.Answer:
                result.append(item.text)
        except AttributeError as err:
            # print(err)
            if "no such child: Answer" in str(err):
                result.append(
                    "ERROR: "
                    + rel_result.objectify_text(rel_result.text).Query.Error.text
                )
            else:
                raise
        return result

    def session_relevance_string(self, relevance, **kwargs):
        """Get Session Relevance Results string"""
        rel_result_array = self.session_relevance_array(relevance, **kwargs)
        return "\n".join(rel_result_array)

    def login(self):
        """do login"""
        return bool(self.get("login").request.status_code == 200)

    def logout(self):
        """clear session and close it"""
        self.session.auth = None
        self.session.cookies.clear()
        self.session.close()

    __call__ = login


class RESTResult:
    """BigFix REST API Result Abstraction Class"""

    def __init__(self, request):
        self.request = request
        self.text = request.text
        self._besxml = None
        self._besobj = None

        if (
            "content-type" in request.headers
            and request.headers["content-type"] == "application/xml"
        ):
            self.valid = True
        elif type(request.text) is str and self.validate_xsd(
            request.text.encode("utf-8")
        ):
            self.valid = True
        else:
            if self.validate_xsd(request.text):
                self.valid = True
            else:
                # print("WARNING: response appears invalid")
                self.valid = False

    def __str__(self):
        if self.valid:
            # I think this is needed for python3 compatibility:
            try:
                return self.besxml.decode("utf-8")
            except BaseException:
                return self.besxml
        else:
            return self.text

    def __call__(self):
        return self.besobj

    @property
    def besxml(self):
        """property for parsed xml representation"""
        if self.valid and self._besxml is None:
            self._besxml = self.xmlparse_text(self.text)

        return self._besxml

    @property
    def besobj(self):
        """property for xml object representation"""
        if self.valid and self._besobj is None:
            self._besobj = self.objectify_text(self.text)

        return self._besobj

    def validate_xsd(self, doc):
        """validate results using XML XSDs"""
        try:
            xmldoc = etree.fromstring(doc)
        except BaseException:
            return False

        for xsd in ["BES.xsd", "BESAPI.xsd", "BESActionSettings.xsd"]:
            xmlschema_doc = etree.parse(resource_filename(__name__, "schemas/%s" % xsd))

            # one schema may throw an error while another will validate
            try:
                xmlschema = etree.XMLSchema(xmlschema_doc)
            except etree.XMLSchemaParseError as err:
                # this should only error if the XSD itself is malformed
                print(f"ERROR with {xsd}: {err}")
                raise

            if xmlschema.validate(xmldoc):
                return True

        return False

    def xmlparse_text(self, text):
        """parse response text as xml"""
        if type(text) is str:
            root_xml = etree.fromstring(text.encode("utf-8"))
        else:
            root_xml = text

        return etree.tostring(root_xml, encoding="utf-8", xml_declaration=True)

    def objectify_text(self, text):
        """parse response text as objectified xml"""
        if type(text) is str:
            root_xml = text.encode("utf-8")
        else:
            root_xml = text

        return objectify.fromstring(root_xml)


def main():
    """if invoked directly, run bescli command loop"""
    # pylint: disable=import-outside-toplevel
    try:
        from bescli import bescli
    except (ImportError, ModuleNotFoundError):
        site.addsitedir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from bescli import bescli
    bescli.main()


if __name__ == "__main__":
    main()
