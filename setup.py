#!/usr/bin/env python

try:
    from distutils.core import setup
except:
    from setuptools import setup

setup(name='besapi',
      version='0.5',
      py_modules=['besapi'],
      package_data={
          'besapi': ['schemas/*.xsd'],
      },
      install_requires={
          'requests',
          'lxml',
      },)
