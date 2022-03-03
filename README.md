besapi
======

besapi is a Python library designed to interact with the BigFix [REST API](https://developer.bigfix.com/rest-api/api/).

Installation:

```pip install besapi```


Usage:
```
import besapi
b = besapi.BESConnection('my_username', 'my_password', 'https://rootserver.domain.org:52311')
rr = b.get('sites')

# rr.request contains the original request object
# rr.text contains the raw request.text data returned by the server
# rr.besxml contains the XML string converted from the request.text
# rr.besobj contains the requested lxml.objectify.ObjectifiedElement

>>>print rr
```
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
```


Command-Line Interface
============
```
$ python bescli.py
OR
>>> import bescli
>>> bescli.main()

BES> login
User [mah60]: mah60
Root Server (ex. https://server.institution.edu:52311): https://my.company.org:52311
Password: 
Login Successful!
BES> get help
...
BES> get sites
...
BES> get sites.OperatorSite.Name
mah60
BES> get help/fixlets
GET:
/api/fixlets/{site}
POST:
/api/fixlets/{site}
BES> get fixlets/operator/mah60
...
```


REST API Help
============
- https://developer.bigfix.com/rest-api/
- http://bigfix.me/restapi


Requirements
============

- Python 3.6 or later
  - version 1.1.3 of besapi was the last to have partial python2 support
- lxml
- requests
- cmd2


Related Items
=======
- https://forum.bigfix.com/t/rest-api-python-module/2170
- https://gist.github.com/hansen-m/58667f370047af92f634
- https://docs.google.com/presentation/d/1pME28wdjkzj9378py9QjFyMOyOHcamB6bk4k8z-c-r0/edit#slide=id.g69e753e75_039
- https://forum.bigfix.com/t/bigfix-documentation-resources/12540
- https://forum.bigfix.com/t/query-for-finding-who-deleted-tasks-fixlets/13668/6
- https://forum.bigfix.com/t/rest-api-java-wrapper/12693


LICENSE
=======
- GNU General Public License v2
