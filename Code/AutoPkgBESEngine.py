#!/usr/bin/python
#
# Copyright 2013 The Pennsylvania State University.
#
"""
AutoPkgBESEngine.py

Created by Matt Hansen (mah60@psu.edu) on 2013-10-08.

AutoPkg Processor for BES (BigFix) XML Tasks and Fixlets
"""
import os
import hashlib
import getpass
import datetime
import subprocess
import urllib2
import xml.dom.minidom

from time import gmtime, strftime
from FoundationPlist import FoundationPlist
from autopkglib import Processor, ProcessorError
from collections import OrderedDict

__all__ = ["AutoPkgBESEngine"]
__version__ = '0.32'

QNA = '/Applications/Utilities/QnA.app/Contents/Resources/QnA'

class AutoPkgBESEngine(Processor):
    """
    AutoPkg Processor for BES (BigFix) XML Tasks and Fixlets
    """

    description = "Generates BigFix XML to install application."
    input_variables = {
        "bes_overrideurl": {
            "required": False,
            "description":
                "Custom override for the prefetch url, defaults to %url%."
        },
        "bes_softwareinstaller": {
            "required": False,
            "description":
                "Path to the installer for prefetch, defaults to %pathname%"
        },
        "bes_filename": {
            "required": False,
            "description":
                "Filename for prefetch command, defaults to tail of the URL"
        },
        "bes_prefetch": {
            "required": False,
            "description":
                "Prefetch to prepend to action, usually provided by BESUploader"
        },
        "bes_version": {
            "required": True,
            "description":
                "Version string for relevance, usually provided by Versioner"
        },
        "bes_title": {
            "required": False,
            "description":
                "Task title, defaults to 'Deploy %name% %version%'"
        },
        "bes_description": {
            "required": False,
            "description": (
                "Task description, defaults to "
                "'This task will install %name% %version%'")
        },
        "bes_category": {
            "required": False,
            "description":
                "Appliation category, defaults to 'Software Deployment'"
        },
        "bes_relevance": {
            "required": True,
            "description":
                "Appliation category, defaults to 'Software Deployment'"
        },
        "bes_actions": {
            "required": True,
            "description":
                "A nested dictionary of a single action or multiple actions."
        }
    }
    output_variables = {
        "bes_file": {
            "description":
                "The file path to the final .bes file."
        },
    }
    __doc__ = description

    def __init__(self, env):
        self.env = env
        self.doc = xml.dom.minidom.Document()

    def get_direct_url(self, url):
        """
        Return a direct url for a download link and spoof the User-Agent.
        """

        useragentsplist = ('/Applications/Safari.app'
                           '/Contents/Resources/UserAgents.plist')

        useragent = FoundationPlist.readPlist(useragentsplist)[0]['user-agent']

        headers = {'User-Agent' : useragent.encode('ascii')}
        request = urllib2.Request(url, None, headers)

        return urllib2.urlopen(request).geturl()

    def get_prefetch(self, file_path, file_name, url):
        """
        Return a prepared prefetch statement string.
        """

        sha1 = hashlib.sha1(file(file_path).read()).hexdigest()
        size = os.path.getsize(file_path)

        return "prefetch %s sha1:%s size:%d %s" % (file_name, sha1, size, url)

    def new_node(self, element_name, node_text="", element_attributes={}):
        """
        Creates a new generic node of either CDATA or Text.
        Optionally adds attributes. Returns the new element.
        """

        new_element = self.doc.createElement(element_name)

        if node_text:
            if any((character in """<>&'\"""") for character in node_text):
                new_element.appendChild(self.doc.createCDATASection(node_text))
            else:
                new_element.appendChild(self.doc.createTextNode(node_text))

        if element_attributes:
            for attrib in element_attributes:
                new_element.setAttribute(attrib, element_attributes[attrib])

        return new_element

    def new_mime(self, mime_name, mime_value):
        """
        Creates a new MIME element. Returns the new MIME element.
        """

        new_mime_element = self.doc.createElement('MIMEField')

        new_mime_element.appendChild(self.new_node('Name', mime_name))
        new_mime_element.appendChild(self.new_node('Value', mime_value))

        return new_mime_element

    def new_link_description(self, description):
        """
        Creates action link description. Returns the description element.
        """

        new_descr_element = self.doc.createElement('Description')

        new_descr_element.appendChild(self.new_node('PreLink', description[0]))
        new_descr_element.appendChild(self.new_node('Link', description[1]))
        new_descr_element.appendChild(self.new_node('PostLink', description[2]))

        return new_descr_element

    def new_action(self, action_dict):
        """
        Create new action from a dictionary. Returns the new action.
        """
        if not action_dict.get('Description', False):
            action_dict['Description'] = [
                '%s - Click ' % action_dict['ActionNumber'],
                'here',
                ' to take action.']

        if not action_dict.get('SuccessCriteria', False):
            action_dict['SuccessCriteria'] = 'OriginalRelevance'

        new_action_element = self.new_node(action_dict['ActionName'],
                                           None,
                                           {'ID': action_dict['ActionNumber']})

        new_action_element.appendChild(
            self.new_link_description(action_dict['Description']))

        new_action_element.appendChild(
            self.new_node('ActionScript',
                          action_dict['ActionScript'],
                          {'MIMEType': 'application/x-Fixlet-Windows-Shell'}))

        new_action_element.appendChild(
            self.new_node('SuccessCriteria',
                          None,
                          {'Option': action_dict['SuccessCriteria']}))

        return new_action_element

    def validate_relevance(self, relevance):
        """
        Validate a line of relevance by parsing the output of the QnA utility.
        """
        try:
            proc = subprocess.Popen(QNA,
                                    bufsize=-1,
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            out, err = proc.communicate(relevance)

            output = {}
            for line in out.strip().split('\n'):
                output[line.split(':')[0].strip()] = line.split(':')[1].strip()

            if output.get('E', None):
                self.output("Relevance Error: {%s} -- %s" %
                            (relevance,
                             output.get('E')))
            return True
        except Exception, error:
            self.output("Relevance Error: (%s) -- %s" % (QNA, error))
            return True

    def main(self):
        """
        Create a BES software distribution task.
        """

        # Assign Application Variables
        url = self.get_direct_url(
            self.env.get("bes_overrideurl",
                         self.env.get("url")))

        bes_displayname = self.env.get("NAME")

        bes_version = self.env.get("bes_version")

        bes_title = self.env.get("bes_title",
                                 "Deploy %s %s" %
                                 (bes_displayname, bes_version))

        bes_category = self.env.get("bes_category", 'Software Deployment')

        bes_relevance = self.env.get("bes_relevance")

        bes_filename = self.env.get("bes_filename", url.split('/')[-1])
        bes_filename = bes_filename.strip().replace(' ', '_')

        bes_prefetch = self.env.get("bes_prefetch",
                                    self.get_prefetch(
                                        self.env.get("bes_softwareinstaller",
                                                     self.env.get("pathname")),
                                        bes_filename, url))

        bes_description = self.env.get("bes_description",
                                       'This task will deploy %s %s.<BR><BR>'
                                       'This task is applicable on Mac OS X' %
                                       (bes_displayname, bes_version))

        bes_actions = self.env.get("bes_actions",
                                   {1:{'ActionName': 'DefaultAction',
                                       'ActionNumber': 'Action1',
                                       'ActionScript': """"""}})

        bes_preactionscript = self.env.get("bes_preactionscript", "")
        bes_postactionscript = self.env.get("bes_postactionscript", "")

        # Prepend prefetch line to action script for all actions
        # Prepend and append pre and post actionscript additions
        for action in bes_actions:
            bes_actions[action]['ActionScript'] = ("%s\n%s%s\n%s" % (
                bes_preactionscript,
                bes_prefetch,
                bes_actions[action]['ActionScript'],
                bes_postactionscript
            )).strip()

        # Additional Metadata for Task
        details = OrderedDict((
            ('Category', bes_category),
            ('DownloadSize',
             str(os.path.getsize(self.env.get(
                 "bes_softwareinstaller", self.env.get("pathname"))))),
            ('Source', "%s v%s" % (os.path.basename(__file__), __version__)),
            ('SourceID', getpass.getuser()),
            ('SourceReleaseDate', str(datetime.datetime.now())[:10]),
            ('SourceSeverity', ""),
            ('CVENames', ""),
            ('SANSID', ""),
        ))

        # Start Building BES XML
        self.output("Building 'Deploy %s %s.bes'" %
                    (bes_displayname, bes_version))

        root_schema = {
            'xmlns:xsi':'http://www.w3.org/2001/XMLSchema-instance',
            'xsi:noNamespaceSchemaLocation': 'BES.xsd'
        }

        root = self.new_node('BES', None, root_schema)

        self.doc.appendChild(root)

        # Create Top Level 'Task' Tag
        node = self.new_node('Task', None)
        root.appendChild(node)

        # Append Title and Description
        node.appendChild(self.new_node('Title', bes_title))
        node.appendChild(self.new_node('Description', bes_description))

        # Append Relevance
        for line in bes_relevance:
            if os.path.isfile(QNA):
                self.validate_relevance(line)
                node.appendChild(self.new_node('Relevance', line))
            else:
                node.appendChild(self.new_node('Relevance', line))

        # Append Details Dictionary
        for key, value in details.items():
            node.appendChild(self.new_node(key, value))

        # Append MIME Source Data
        node.appendChild(self.new_mime('x-fixlet-source',
                                       os.path.basename(__file__)))
        node.appendChild(
            self.new_mime('x-fixlet-modification-time',
                          strftime("%a, %d %b %Y %X +0000", gmtime())))

        node.appendChild(self.new_node('Domain', 'BESC'))

        # Append Default Action
        for action in sorted(bes_actions.iterkeys()):
            if bes_actions[action].get('ActionName', None) == 'DefaultAction':
                node.appendChild(self.new_action(bes_actions[action]))
                bes_actions.pop(action, None)

        # Append Actions
        for action in sorted(bes_actions.iterkeys()):
            node.appendChild(self.new_action(bes_actions[action]))

        # Write Final BES File to Disk
        outputfile_handle = open("%s/Deploy %s %s.bes" %
                                 (self.env.get("RECIPE_CACHE_DIR"),
                                  bes_displayname, bes_version), "wb")

        outputfile_handle.write(self.doc.toxml(encoding="UTF-8"))
        outputfile_handle.close()

        self.env['bes_file'] = outputfile_handle.name
        self.output("Output BES File: '%s'" % self.env.get("bes_file"))

if __name__ == "__main__":
    processor = AutoPkgBESEngine()
    processor.execute_shell()
    