#!/usr/bin/python
# encoding: utf-8
#
# Copyright 2015 The Pennsylvania State University.
#
"""
BESTemplater.py

Created by Matt Hansen (mah60@psu.edu) on 2015-04-30.

AutoPkg Processor for importing tasks using the BigFix RESTAPI
"""

import os
import sys

from autopkglib import Processor, ProcessorError

__all__ = ["BESTemplater"]

class BESTemplater(Processor):
    """AutoPkg Processor for rendering tasks from templates"""
    description = "Generates BigFix XML to install application."
    input_variables = {
        "template_name": {
            "required": True,
            "description":
                "Name of template file."
        },
    }
    output_variables = {
        "bes_file": {
            "description":
                "The resulting BES task rendered from the template."
        },
    }
    __doc__ = description


    def main(self):
        """BESImporter Main Method"""
        
        # http://stackoverflow.com/a/14150750/2626090
        uppath = lambda _path, n: os.sep.join(_path.split(os.sep)[:-n])

        try:
            from jinja2 import Environment, ChoiceLoader, FileSystemLoader
        except ImportError as err:
            raise ProcessorError("jinja2 module is not installed: %s" % err)
        
        # Assign variables
        template_name = self.env.get("template_name")
        name = self.env.get("NAME")
        version = self.env.get("version")
        RECIPE_DIR = self.env.get("RECIPE_DIR")
        BES_TEMPLATES = self.env.get("BES_TEMPLATES")
        
        jinja_env = Environment(loader = ChoiceLoader([
            FileSystemLoader(os.getcwd()),
            FileSystemLoader('templates'),
            FileSystemLoader(os.path.join(RECIPE_DIR, 'templates')),
            FileSystemLoader(os.path.join(uppath(RECIPE_DIR, 1), 'templates')),
            FileSystemLoader(os.path.join(uppath(RECIPE_DIR, 2), 'Templates')),
            FileSystemLoader(BES_TEMPLATES)
        ]))
        
        template_task = jinja_env.get_template(template_name)
        # print jinja_env.list_templates()
        rendered_task = template_task.render(**self.env)
        
        # Write Final BES File to Disk
        outputfile_handle = open("%s/Deploy %s %s.bes" %
                                 (self.env.get("RECIPE_CACHE_DIR"),
                                  name, version), "wb")

        outputfile_handle.write(rendered_task)
        outputfile_handle.close()

        self.env['bes_file'] = outputfile_handle.name
        self.output("Output BES File: '%s'" % self.env.get("bes_file"))

if __name__ == "__main__":
    processor = BESImporter()
    processor.execute_shell()
