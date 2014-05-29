#!/usr/bin/env python

from distutils.core import setup

setup(name='besapi',
      version='0.4',
      py_modules=['besapi'],
      package_data={
        'besapi': ['schemas/*.xsd'],
      },
      install_requires={
        'requests',
        'lxml',
      },        
      )