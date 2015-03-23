python-besapi
======

python-besapi is a Python library designed to interact with the BES (BigFix) REST API.

Installation:

    pip install -U -e git+https://github.com/CLCMacTeam/besapi.git#egg=besapi


Usage:
    
    import besapi
    b = besapi.BESConnection('my_username', 'my_password', 'https://rootserver.domain.org:52311')
    rr = b.get('sites')
    
    # rr.request contains the original request object
    # rr.text contains the raw request.text data returned by the server
    # rr.besxml contains the XML string converted from the request.text
    # rr.besobj contains the requested lxml.objectify.ObjectifiedElement
    
    >>>print rr
```xml
<BESAPI xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="BESAPI.xsd">
	<ExternalSite Resource="http://rootserver.domain.org:52311/api/site/external/BES%20Support">
		<Name>BES Support</Name>
	</ExternalSite>
	<!---...--->
	<CustomSite Resource="http://rootserver.domain.org:52311/api/site/custom/Org">
		<Name>Org</Name>
	</CustomSite>
	<CustomSite Resource="http://rootserver.domain.org:52311/api/site/custom/Org%2fMac">
		<Name>Org/Mac</Name>
	</CustomSite>
	<CustomSite Resource="http://rootserver.domain.org:52311/api/site/custom/Org%2fWindows">
		<Name>Org/Windows</Name>
	</CustomSite>
	<CustomSite Resource="http://rootserver.domain.org:52311/api/site/custom/ContentDev">
		<Name>ContentDev</Name>
	</CustomSite>
	<OperatorSite Resource="http://rootserver.domain.org:52311/api/site/operator/mah60">
		<Name>mah60</Name>
	</OperatorSite>
	<ActionSite Resource="http://rootserver.domain.org:52311/api/site/master">
		<Name>ActionSite</Name>
	</ActionSite>
</BESAPI>
```
    >>>rr.besobj.attrib
    {'{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation': 'BESAPI.xsd'}
    
    >>>rr.besobj.ActionSite.attrib
    {'Resource': 'http://rootserver.domain.org:52311/api/site/master'}
    
    >>>rr.besobj.ActionSite.attrib['Resource']
    'http://rootserver.domain.org:52311/api/site/master'
    
    >>>rr.besobj.ActionSite.Name
    'ActionSite'
    
    >>>rr.besobj.OperatorSite.Name
    'mah60'
    
    >>>for cSite in rr.besobj.CustomSite:
    ...     print cSite.Name
    Org
    Org/Mac
    Org/Windows
    ContentDev
    ...
    
    >>>rr = b.get('task/operator/mah60/823975')
    >>>with open('/Users/Shared/Test.bes", "wb") as file:
    ...     file.write(rr.text)
    
    >>>b.delete('task/operator/mah60/823975')
    
    >>> file = open('/Users/Shared/Test.bes')
    >>> b.post('tasks/operator/mah60', file)
    >>> b.put('task/operator/mah60/823975', file)

Command-Line Interface
============
```
BES> login
User [bfadmin]: username
Root Server (ex. https://server.institution.edu:52311): https://my.company.org:52311
Password: 
Login Successful!
BES> get help
...
BES> get sites
...
```

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
