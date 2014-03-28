python-besapi
======

python-besapi is a Python library designed to interact with the BES (BigFix) REST API.

Installation:

    pip install -U -e git+https://git@stash.tlt.psu.edu:8443/scm/sys/besapi.git#egg=besapi


Usage:
    
    import besapi
    b = besapi.BESConnection('my_username', 'my_password', 'https://myrootserver.organization.tld:52311')
    rr = b.getREST('the/api/path') # Examples - '/help' or http://bigfix.me/restapi
    
    rr.besobj contains the requested lxml.objectify.ObjectifiedElement
    rr.result contains the XML string converted from byteArray
    rr.byteArray contains the raw byte array returned by the server
    

Requirements
============

- Python 2.7 or later
- lxml
- requests


LICENSE
=======
Copyright (c) 2014, The Pennsylvania State University
All rights reserved.