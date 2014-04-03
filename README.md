python-besapi
======

python-besapi is a Python library designed to interact with the BES (BigFix) REST API.

Installation:

    pip install -U -e git+https://stash.tlt.psu.edu:8443/scm/sys/besapi.git#egg=besapi


Usage:
    
    import besapi
    b = besapi.BESConnection('my_username', 'my_password', 'https://bes.win.psu.edu:52311')
    rr = b.getREST('sites')
    
    # rr.bytearray contains the raw unicode byte array returned by the server
    # rr.result contains the XML string converted from bytearray
    # rr.besobj contains the requested lxml.objectify.ObjectifiedElement
    
    >>>print rr
    <BESAPI xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="BESAPI.xsd">
	<ExternalSite Resource="http://bes.win.psu.edu:52311/api/site/external/BES%20Support">
		<Name>BES Support</Name>
	</ExternalSite>
	<!---...--->
   	<CustomSite Resource="http://bes.win.psu.edu:52311/api/site/custom/SysManDev">
	<Name>SysManDev</Name>
	</CustomSite>
	<OperatorSite Resource="http://bes.win.psu.edu:52311/api/site/operator/mah60">
		<Name>mah60</Name>
	</OperatorSite>
	<ActionSite Resource="http://bes.win.psu.edu:52311/api/site/master">
		<Name>ActionSite</Name>
	</ActionSite>
    </BESAPI>
    
    >>>rr.besobj.attrib
    {'{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation': 'BESAPI.xsd'}
    
    >>>rr.besobj.ActionSite.attrib
    {'Resource': 'http://bes.win.psu.edu:52311/api/site/master'}
    
    >>>rr.besobj.ActionSite.attrib['Resource']
    'http://bes.win.psu.edu:52311/api/site/master'
    
    >>>rr.besobj.ActionSite.Name
    'ActionSite'
    
    
REST API Help
============
http://bigfix.me/restapi
    

Requirements
============

- Python 2.7 or later
- lxml
- requests


LICENSE
=======
Copyright (c) 2014, The Pennsylvania State University
All rights reserved.