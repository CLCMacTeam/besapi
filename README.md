<<<<<<< HEAD
AutoPkg BESEngine
=======

AutoPkgBESEngine is a collection of shared processors for [AutoPkg](https://github.com/autopkg/autopkg) used to automatically create and import software deployment tasks into a [IBM Endpoint Manager](http://www.ibm.com/software/tivoli/solutions/endpoint-manager/) console.

AutoPkgBESEngine.py     - AutoPkg Processor for BES (BigFix) XML Tasks and Fixlets

BESImporter.py          - AutoPkg Processor for importing tasks using the BigFix RESTAPI

BESUploader.py          - AutoPkg Processor for uploading files using the BigFix REST API

BESRelevanceProvider.py - AutoPkg Processor for retreiving relevance data for tasks

Installation
------------
***The easy way...***

```
autopkg repo-add https://github.com/autopkg/hansen-m-recipes.git
autopkg run BESEngine.install
```

***The hard way...***

Copy or symlink the BES processors (Code/*.py files) to /Library/AutoPkg/autopkglib.

You can specify your BES console settings directly in the recipes or set them globally:

```
defaults write com.github.autopkg BES_ROOTSERVER yourBESRootServer
defaults write com.github.autopkg BES_USERNAME yourAPIUserAccount
defaults write com.github.autopkg BES_PASSWORD yourAPIUserAccountPassword
```

You must have a copy of QnA.app installed in /Applications/Utilities to use the BESRelevanceProvider processor.

Discussion
----------

Discussion of the use and development of AutoPkg is [here](http://groups.google.com/group/autopkg-discuss).

If you would like to contact the maintainters directly please send an email to clcmac@psu.edu

If you have any questions on getting started we'd be happy to help. Or just let us know if you implement this project in your own organization.

Where can I find BigFix recipes?
----------

Penn State currently has over 100 BigFix recipes for commonly used software. Unfortunately, these recipes include many organization specific settings, file paths and naming conventions. We are in the process of cleaning up these recipes so they can be shared publicly.

We are also working on making it easier to share recipes by adding more flexibility for using recipe overrides so organizations can add their own specific customizations but still take advantage of the shared recipes and to share their own.

You can find example recipes under the "Examples" directory. If you'd like to work with us on getting a recipe for a specific piece of software or have any suggestions for making bigfix recipes easier to share please open an issue or send us an email at clcmac@psu.edu.

Known Issues
----------

- AutoPkgBESEngine only supports the generation of a single prefetch item, but additional prefetch lines can be hardcoded into the recipes.

- BESUploader requires a master operator account. Please vote for this IBM RFE - http://www.ibm.com/developerworks/rfe/execute?use_case=viewRfe&CR_ID=41378

- BESRelevanceProvider only supports a single relevance statement and stores the return value in a statically named variable.


License
----------

Copyright The Pennsylvania State University.
=======
python-besapi
======

python-besapi is a Python library designed to interact with the BES (BigFix) [REST API](https://www.ibm.com/developerworks/community/wikis/home?lang=en#!/wiki/Tivoli%20Endpoint%20Manager/page/RESTAPI%20Action).

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
- http://bigfix.me/restapi
- https://www.ibm.com/developerworks/community/wikis/home?lang=en#!/wiki/Tivoli%20Endpoint%20Manager/page/RESTAPI%20Action

Requirements
============

- Python 2.7 or later
- lxml
- requests


LICENSE
=======
- Copyright (c) 2015, The Pennsylvania State University
- GNU General Public License v2
>>>>>>> 55a580241a5846e23331c85f3bf269eae9f85d9a
