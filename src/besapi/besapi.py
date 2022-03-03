#!/usr/bin/env python
# -*- coding: future_fstrings -*-
"""
besapi.py

Created by Matt Hansen (mah60@psu.edu) on 2014-03-20.
Enhancements by James Stewart since 2021

Library for communicating with the BES (BigFix) REST API.
"""

import json
import os
import site
import string
import sys

# import urllib3.poolmanager

try:
    from urllib import parse
except ImportError:
    from urlparse import parse_qs as parse

import requests
from lxml import etree, objectify
from pkg_resources import resource_filename


def sanitize_txt(*args):
    """Clean arbitrary text for safe file system usage."""
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)

    sani_args = []
    for arg in args:
        sani_args.append(
            "".join(
                c
                for c in str(arg).replace("/", "-").replace("\\", "-")
                if c in valid_chars
            )
            .encode("ascii", "ignore")
            .decode()
        )

    return tuple(sani_args)


def elem2dict(node):
    """
    Convert an lxml.etree node tree into a dict.
    https://gist.github.com/jacobian/795571?permalink_comment_id=2981870#gistcomment-2981870
    """
    result = {}

    for element in node.iterchildren():
        # Remove namespace prefix
        key = element.tag.split("}")[1] if "}" in element.tag else element.tag

        # Process element as tree element if the inner XML contains non-whitespace content
        if element.text and element.text.strip():
            value = element.text
        else:
            value = elem2dict(element)
        if key in result:

            if type(result[key]) is list:
                result[key].append(value)
            else:
                tempvalue = result[key].copy()
                result[key] = [tempvalue, value]
        else:
            result[key] = value
    return result


# # https://docs.python-requests.org/en/latest/user/advanced/#transport-adapters
# class HTTPAdapterBiggerBlocksize(requests.adapters.HTTPAdapter):
#     """custom HTTPAdapter for requests to override blocksize
#     for Uploading or Downloading large files"""

#     # override inti_poolmanager from regular HTTPAdapter
#     # https://stackoverflow.com/questions/22915295/python-requests-post-and-big-content/22915488#comment125583017_22915488
#     def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
#         """Initializes a urllib3 PoolManager.

#         This method should not be called from user code, and is only
#         exposed for use when subclassing the
#         :class:`HTTPAdapter <requests.adapters.HTTPAdapter>`.

#         :param connections: The number of urllib3 connection pools to cache.
#         :param maxsize: The maximum number of connections to save in the pool.
#         :param block: Block when no free connections are available.
#         :param pool_kwargs: Extra keyword arguments used to initialize the Pool Manager.
#         """
#         # save these values for pickling
#         self._pool_connections = connections
#         self._pool_maxsize = maxsize
#         self._pool_block = block

#         # This doesn't work until urllib3 is updated to a future version:
#         # updating blocksize to be larger:
#         # pool_kwargs["blocksize"] = 8 * 1024 * 1024

#         self.poolmanager = urllib3.poolmanager.PoolManager(
#             num_pools=connections,
#             maxsize=maxsize,
#             block=block,
#             strict=True,
#             **pool_kwargs,
#         )


class BESConnection:
    """BigFix RESTAPI connection abstraction class"""

    def __init__(self, username, password, rootserver, verify=False):

        if not verify:
            # disable SSL warnings
            requests.packages.urllib3.disable_warnings()  # pylint: disable=no-member

        self.username = username
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

        self.login()

    def __repr__(self):
        """object representation"""
        # https://stackoverflow.com/a/2626364/861745
        return f"Object: besapi.BESConnction( username={self.username}, rootserver={self.rootserver} )"

    def __eq__(self, other):
        if (
            self.rootserver == other.rootserver
            and self.session.auth == other.session.auth
            and self.verify == other.verify
        ):
            return True
        return False

    def __del__(self):
        """cleanup on deletion of instance"""
        self.logout()
        self.session.auth = None

    def __bool__(self):
        """get true or false"""
        return self.login()

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
                data=f"relevance={parse.quote(relevance, safe=':+')}",
                verify=self.verify,
                **kwargs
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

    def connected(self):
        """return true if connected"""
        return bool(self.get("login").request.status_code == 200)

    def login(self):
        """do login"""
        if not self.connected():
            self.get("login").request.raise_for_status()

        # This doesn't work until urllib3 is updated to a future version:
        # if self.connected():
        #     self.session.mount(self.url("upload"), HTTPAdapterBiggerBlocksize())

        return self.connected()

    def logout(self):
        """clear session and close it"""
        self.session.cookies.clear()
        self.session.close()

    def upload(self, file_path, file_name=None):
        """
        upload a single file
        https://developer.bigfix.com/rest-api/api/upload.html
        """
        if not os.access(file_path, os.R_OK):
            print(file_path, "is not readable")
            raise FileNotFoundError

        # if file_name not specified, then get it from tail of file_path
        if not file_name:
            file_name = os.path.basename(file_path)

        # Example Header::  Content-Disposition: attachment; filename="file.xml"
        headers = {"Content-Disposition": f'attachment; filename="{file_name}"'}
        with open(file_path, "rb") as f:
            return self.post(self.url("upload"), data=f, headers=headers)

    def export_site_contents(
        self, site_path, export_folder="./", name_trim=70, verbose=False
    ):
        """export contents of site
        Originally here:
        - https://gist.github.com/jgstew/1b2da12af59b71c9f88a
        - https://bigfix.me/fixlet/details/21282
        """
        if verbose:
            print("export_site_contents()")
        # Iterate Over All Site Content
        content = self.get("site/" + site_path + "/content")
        if verbose:
            print(content)
        if content.request.status_code == 200:
            print(
                "Archiving %d items from %s..." % (content().countchildren(), site_path)
            )

            for item in content().iterchildren():
                if verbose:
                    print(
                        "{%s} (%s) [%s] %s - %s    "
                        % (
                            site_path,
                            item.tag,
                            item.ID,
                            item.Name.text,
                            item.attrib["LastModified"],
                        )
                    )

                # Get Specific Content
                content = self.get(
                    item.attrib["Resource"].replace("http://", "https://")
                )

                # Write Content to Disk
                if content:
                    if not os.path.exists(
                        export_folder + "%s/%s" % sanitize_txt(site_path, item.tag)
                    ):
                        os.makedirs(
                            export_folder + "%s/%s" % sanitize_txt(site_path, item.tag)
                        )

                    with open(
                        export_folder
                        + "%s/%s/%s - %s.bes"
                        % sanitize_txt(
                            site_path,
                            item.tag,
                            item.ID,
                            # http://stackoverflow.com/questions/2872512/python-truncate-a-long-string
                            # trimming to 150 worked in most cases, but recently even that had issues.
                            # now trimmed to first name_trim characters of the title of the item.
                            item.Name.text[:name_trim]
                        ),
                        "wb",
                    ) as bes_file:
                        bes_file.write(content.text.encode("utf-8"))

    def export_all_sites(
        self, include_external=False, export_folder="./", name_trim=70, verbose=False
    ):
        """export all bigfix sites to a folder"""
        results_sites = self.get("sites")
        if verbose:
            print(results_sites)
        if results_sites.request.status_code == 200:
            for item in results_sites().iterchildren():
                site_path = item.attrib["Resource"].split("/api/site/", 1)[1]
                if include_external or "external/" not in site_path:
                    print("Exporting Site:", site_path)
                    self.export_site_contents(
                        site_path, export_folder, name_trim, verbose
                    )

    __call__ = login
    # https://stackoverflow.com/q/40536821/861745
    __enter__ = login
    __exit__ = logout


class RESTResult:
    """BigFix REST API Result Abstraction Class"""

    def __init__(self, request):
        self.request = request
        self.text = request.text
        self._besxml = None
        self._besobj = None
        self._besdict = None
        self._besjson = None

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

    @property
    def besdict(self):
        """property for python dict representation"""
        if self._besdict is None:
            if self.valid:
                self._besdict = elem2dict(etree.fromstring(self.besxml))
            else:
                self._besdict = {"text": str(self)}

        return self._besdict

    @property
    def besjson(self):
        """property for json representation"""
        if self._besjson is None:
            self._besjson = json.dumps(self.besdict, indent=2)

        return self._besjson

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
