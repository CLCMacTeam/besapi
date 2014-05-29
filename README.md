python-besapi
======

python-besapi is a Python library designed to interact with the BES (BigFix) REST API.

Installation:

    pip install -U -e git+https://stash.tlt.psu.edu:8443/scm/sys/besapi.git#egg=besapi


Usage:
    
    import besapi
    b = besapi.BESConnection('my_username', 'my_password', 'https://bes.win.psu.edu:52311')
    rr = b.get('sites')
    
    # rr.request contains the original request object
    # rr.text contains the raw request.text data returned by the server
    # rr.besxml contains the XML string converted from the request.text
    # rr.besobj contains the requested lxml.objectify.ObjectifiedElement
    
    >>>print rr
```xml
<BESAPI xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="BESAPI.xsd">
	<ExternalSite Resource="http://bes.win.psu.edu:52311/api/site/external/BES%20Support">
		<Name>BES Support</Name>
	</ExternalSite>
	<!---...--->
	<CustomSite Resource="http://bes.win.psu.edu:52311/api/site/custom/PSU">
		<Name>PSU</Name>
	</CustomSite>
	<CustomSite Resource="http://bes.win.psu.edu:52311/api/site/custom/PSU%2fMac">
		<Name>PSU/Mac</Name>
	</CustomSite>
	<CustomSite Resource="http://bes.win.psu.edu:52311/api/site/custom/PSU%2fWindows">
		<Name>PSU/Windows</Name>
	</CustomSite>
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
```
    >>>rr.besobj.attrib
    {'{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation': 'BESAPI.xsd'}
    
    >>>rr.besobj.ActionSite.attrib
    {'Resource': 'http://bes.win.psu.edu:52311/api/site/master'}
    
    >>>rr.besobj.ActionSite.attrib['Resource']
    'http://bes.win.psu.edu:52311/api/site/master'
    
    >>>rr.besobj.ActionSite.Name
    'ActionSite'
    
    >>>rr.besobj.OperatorSite.Name
    'mah60'
    
    >>>for cSite in rr.besobj.CustomSite:
    ...     print cSite.Name
    PSU
    PSU/Mac
    PSU/Windows
    SysManDev
    ...
    
    >>>rr = b.get('task/operator/mah60/823975')
    >>>with open('/Users/Shared/Test.bes", "wb") as file:
    ...     file.write(rr.text)
    
    >>>b.delete('task/operator/mah60/823975')
    
    >>> file = open('/Users/Shared/Test.bes')
    >>> b.post('tasks/operator/mah60', file)
    >>> b.put('task/operator/mah60/823975', file)
    
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