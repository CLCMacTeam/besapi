#!/usr/bin/env python
"""
besapi.py

Created by Matt Hansen (mah60@psu.edu) on 2014-03-20.
Enhancements by James Stewart since 2021

Library for communicating with the BES (BigFix) REST API.
"""

import datetime
import json
import logging
import os
import random
import site
import string

# import urllib3.poolmanager

try:
    from urllib import parse
except ImportError:
    from urlparse import parse_qs as parse

import requests
from lxml import etree, objectify
from pkg_resources import resource_filename

logging.basicConfig(level=logging.WARNING)
besapi_logger = logging.getLogger("besapi")


def rand_password(length=20):
    """get a random password"""

    all_safe_chars = string.ascii_letters + string.digits + "!#()*+,-.:;<=>?[]^_|~"

    # https://medium.com/analytics-vidhya/create-a-random-password-generator-using-python-2fea485e9da9
    password = "".join(random.sample(all_safe_chars, length))
    return password


def sanitize_txt(*args):
    """Clean arbitrary text for safe file system usage."""
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)

    sani_args = []
    for arg in args:
        sani_args.append(
            "".join(
                c
                for c in str(arg).replace("/", "-").replace("\\", "-").replace(" ", "_")
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
        # store info on operator used to login
        # self.operator_info = {}

        # use a sitepath context if none specified when required.
        self.site_path = "master"

        # if not provided, add on https://
        if not rootserver.startswith("http"):
            rootserver = "https://" + rootserver
        # if port not provided, add on the default :52311
        if not rootserver.count(":") == 2:
            rootserver = rootserver + ":52311"

        self.rootserver = rootserver
        self.verify = verify
        self.last_connected = None

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
        # avoid infinite loop:
        if "login" not in path:
            self.login()
        self.last_connected = datetime.datetime.now()
        return RESTResult(
            self.session.get(self.url(path), verify=self.verify, **kwargs)
        )

    def post(self, path, data, **kwargs):
        """HTTP POST request"""
        self.login()
        self.last_connected = datetime.datetime.now()
        return RESTResult(
            self.session.post(self.url(path), data=data, verify=self.verify, **kwargs)
        )

    def put(self, path, data, **kwargs):
        """HTTP PUT request"""
        self.login()
        self.last_connected = datetime.datetime.now()
        return RESTResult(
            self.session.put(self.url(path), data=data, verify=self.verify, **kwargs)
        )

    def delete(self, path, **kwargs):
        """HTTP DELETE request"""
        self.login()
        self.last_connected = datetime.datetime.now()
        return RESTResult(
            self.session.delete(self.url(path), verify=self.verify, **kwargs)
        )

    def session_relevance_xml(self, relevance, **kwargs):
        """Get Session Relevance Results XML"""
        self.login()
        self.last_connected = datetime.datetime.now()
        return RESTResult(
            self.session.post(
                self.url("query"),
                data=f"relevance={parse.quote(relevance, safe=':+')}",
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
        if bool(self.last_connected):
            duration_obj = datetime.datetime.now() - self.last_connected
            duration_minutes = duration_obj / datetime.timedelta(minutes=1)
            besapi_logger.info(
                "Connection Time: `%s` - Duration: %d minutes",
                self.last_connected,
                duration_minutes,
            )
            if int(duration_minutes) > 3:
                besapi_logger.info("Refreshing Login to prevent timeout.")
                self.last_connected = None

        if not bool(self.last_connected):
            result_login = self.get("login")
            if not result_login.request.status_code == 200:
                result_login.request.raise_for_status()
            if result_login.request.status_code == 200:
                # set time of connection
                self.last_connected = datetime.datetime.now()

        # This doesn't work until urllib3 is updated to a future version:
        # if self.connected():
        #     self.session.mount(self.url("upload"), HTTPAdapterBiggerBlocksize())

        return bool(self.last_connected)

    def logout(self):
        """clear session and close it"""
        self.session.cookies.clear()
        self.session.close()

    def validate_site_path(self, site_path, check_site_exists=True, raise_error=False):
        """make sure site_path is valid"""

        if site_path is None:
            if not raise_error:
                return None
            raise ValueError("Site Path is `None` - NoneType Error")
        if str(site_path).strip() == "":
            if not raise_error:
                return None
            raise ValueError("Site Path is empty!")

        # options for valid site prefix: (master must be last, special case)
        site_prefixes = ["external/", "custom/", "operator/", "master"]

        for prefix in site_prefixes:
            if prefix in site_path:
                if prefix == "master" and prefix != site_path:
                    # Invalid: This error should be raised regardless
                    raise ValueError(
                        f"Site path for master actionsite must be `master` not `{site_path}`"
                    )
                if not check_site_exists:
                    # don't check if site exists first
                    return site_path
                else:
                    # check site exists first
                    site_result = self.get(f"site/{site_path}")
                    if site_result.request.status_code != 200:
                        besapi_logger.info("Site `%s` does not exist", site_path)
                        if not raise_error:
                            return None

                        raise ValueError(f"Site at path `{site_path}` does not exist!")

                    # site_path is valid and exists:
                    return site_path

        # Invalid: No valid prefix found
        raise ValueError(
            f"Site Path does not start with a valid prefix! {site_prefixes}"
        )

    def get_current_site_path(self, site_path=None):
        """if site_path is none, get current instance site_path,
        otherwise validate and return provided site_path"""

        # use instance site_path context if none provided:
        if site_path is None or str(site_path).strip() == "":
            site_path = self.site_path

        if site_path is None or str(site_path).strip() == "":
            besapi_logger.error("Site Path context not set and Site Path not provided!")
            raise ValueError("Site Path context not set and Site Path not provided!")

        # don't check for site's existence when doing basic get
        return self.validate_site_path(site_path, check_site_exists=False)

    def set_current_site_path(self, site_path):
        """set current site path context"""

        if self.validate_site_path(site_path):
            self.site_path = site_path
            return self.site_path

    def create_site_from_file(self, bes_file_path, site_type="custom"):
        """create new site"""
        xml_parsed = etree.parse(bes_file_path)
        new_site_name = xml_parsed.xpath("/BES/CustomSite/Name/text()")[0]

        result_site_path = self.validate_site_path(
            site_type + "/" + new_site_name, True, False
        )

        if result_site_path:
            besapi_logger.warning("Site `%s` already exists", result_site_path)
            return None

        result_site = self.post("sites", etree.tostring(xml_parsed))

        return result_site

    def get_user(self, user_name):
        """get a user"""

        result_users = self.get(f"operator/{user_name}")

        if result_users and "Operator does not exist" not in str(result_users):
            return result_users

        besapi_logger.info("User `%s` Not Found!", user_name)

    def create_user_from_file(self, bes_file_path):
        """create user from xml"""
        xml_parsed = etree.parse(bes_file_path)
        new_user_name = xml_parsed.xpath("/BESAPI/Operator/Name/text()")[0]
        result_user = self.get_user(new_user_name)

        if result_user:
            besapi_logger.warning("User `%s` Already Exists!", new_user_name)
            return result_user
        besapi_logger.info("Creating User `%s`", new_user_name)
        _ = self.post("operators", etree.tostring(xml_parsed))
        # print(user_result)
        return self.get_user(new_user_name)

    def get_computergroup(self, group_name, site_path=None):
        """get computer group resource URI"""

        site_path = self.get_current_site_path(site_path)
        result_groups = self.get(f"computergroups/{site_path}")

        for group in result_groups.besobj.ComputerGroup:
            if group_name == str(group.Name):
                besapi_logger.info(
                    "Found Group With Resource: %s", group.attrib["Resource"]
                )
                return group

        besapi_logger.info("Group `%s` Not Found!", group_name)

    def create_group_from_file(self, bes_file_path, site_path=None):
        """create a new group"""
        site_path = self.get_current_site_path(site_path)
        xml_parsed = etree.parse(bes_file_path)
        new_group_name = xml_parsed.xpath("/BES/ComputerGroup/Title/text()")[0]

        existing_group = self.get_computergroup(new_group_name, site_path)

        if existing_group is not None:
            besapi_logger.warning("Group `%s` Already Exists!", new_group_name)
            return existing_group

        # print(lxml.etree.tostring(xml_parsed))

        _ = self.post(f"computergroups/{site_path}", etree.tostring(xml_parsed))

        return self.get_computergroup(site_path, new_group_name)

    def upload(self, file_path, file_name=None):
        """
        upload a single file
        https://developer.bigfix.com/rest-api/api/upload.html
        """
        if not os.access(file_path, os.R_OK):
            besapi_logger.error(file_path, "is not readable")
            raise FileNotFoundError

        # if file_name not specified, then get it from tail of file_path
        if not file_name:
            file_name = os.path.basename(file_path)

        # Example Header::  Content-Disposition: attachment; filename="file.xml"
        headers = {"Content-Disposition": f'attachment; filename="{file_name}"'}
        with open(file_path, "rb") as f:
            return self.post(self.url("upload"), data=f, headers=headers)

    def get_content_by_resource(self, resource_url):
        """get a single content item by resource"""
        # Get Specific Content
        content = None
        try:
            content = self.get(resource_url.replace("http://", "https://"))
        except PermissionError as err:
            logging.error("Could not export item:")
            logging.error(err)

        # item_id = int(resource_url.split("/")[-1])
        # site_name = resource_url.split("/")[-2]
        # if site_name == "master":
        #     site_path = site_name
        # else:
        #     site_path = resource_url.split("/")[-3] + "/" + site_name
        return content

    def export_site_contents(
        self,
        site_path=None,
        export_folder="./",
        name_trim=100,
        verbose=False,
        include_site_folder=True,
        include_item_ids=True,
    ):
        """export contents of site
        Originally here:
        - https://gist.github.com/jgstew/1b2da12af59b71c9f88a
        - https://bigfix.me/fixlet/details/21282
        """
        site_path = self.get_current_site_path(site_path)
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
                content = self.get_content_by_resource(item.attrib["Resource"])

                if not content:
                    continue

                # Write Content to Disk
                item_folder = export_folder + "%s/%s" % sanitize_txt(
                    site_path, item.tag
                )
                if not include_site_folder:
                    item_folder = export_folder + "%s" % sanitize_txt(item.tag)
                if not os.path.exists(item_folder):
                    os.makedirs(item_folder)

                item_path = export_folder + "%s/%s/%s-%s.bes" % sanitize_txt(
                    site_path,
                    item.tag,
                    item.ID,
                    item.Name.text[:name_trim],
                )
                if not include_item_ids:
                    item_path = export_folder + "%s/%s/%s.bes" % sanitize_txt(
                        site_path,
                        item.tag,
                        item.Name.text[:name_trim],
                    )
                if not include_site_folder:
                    item_path = export_folder + "%s/%s-%s.bes" % sanitize_txt(
                        item.tag,
                        item.ID,
                        item.Name.text[:name_trim],
                    )
                    if not include_item_ids:
                        item_path = export_folder + "%s/%s.bes" % sanitize_txt(
                            item.tag,
                            item.Name.text[:name_trim],
                        )
                with open(
                    item_path,
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


class RESTResult:
    """BigFix REST API Result Abstraction Class"""

    def __init__(self, request):
        self.request = request
        self.text = request.text
        self._besxml = None
        self._besobj = None
        self._besdict = None
        self._besjson = None

        try:
            if self.request.status_code == 403:
                # Error most likely due to not having master operator privs
                # Could also be due to non-master operator not having specific privs
                raise PermissionError(
                    f"\n - HTTP Response Status Code: `403` Forbidden\n - ERROR: `{self.text}`\n - URL: `{self.request.url}`"
                )

            besapi_logger.info(
                "HTTP Request Status Code `%d` from URL `%s`",
                self.request.status_code,
                self.request.url,
            )
        except AttributeError as err:
            besapi_logger.warning("Error (expected during tests) %s", err)

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
                besapi_logger.error("ERROR with `%s`: %s", xsd, err)
                raise err

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
    except ImportError:
        site.addsitedir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from bescli import bescli
    bescli.main()


if __name__ == "__main__":
    main()
