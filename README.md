AutoPkg BESEngine
=======

AutoPkgBESEngine is a collection of shared processors for AutoPkg (https://github.com/autopkg/autopkg) used to automatically create and import software deployment tasks into a IBM Endpoint Manager console (http://www.ibm.com/software/tivoli/solutions/endpoint-manager/).

AutoPkgBESEngine.py     - AutoPkg Processor for BES (BigFix) XML Tasks and Fixlets

BESImporter.py          - AutoPkg Processor for importing tasks using the BigFix RESTAPI

BESUploader.py          - AutoPkg Processor for uploading files using the BigFix REST API

BESRelevanceProvider.py - AutoPkg Processor for retreiving relevance data for tasks

Installation
------------

Copy or symlink the BES processors (Code/*.py files) to /Library/AutoPkg/autopkglib.

You can specify your BES console settings directly in the recipes or set them globally:

defaults write com.github.autopkg BES_ROOTSERVER yourBESRootServer
defaults write com.github.autopkg BES_USERNAME yourAPIUserAccount
defaults write com.github.autopkg BES_PASSWORD yourAPIUserAccountPassword

You must have a copy of QnA.app installed in /Applications/Utilities to use the BESRelevanceProvider processor.

Discussion
----------

Discussion of the use and development of AutoPkg is [here](http://groups.google.com/group/autopkg-discuss).

If you would like to contact the maintainters directly please send an email to clcmac@psu.edu

If you have any questions on getting started we'd be happy to help. Or just let us know if you implement this project in your own organization.

Where can I find BigFix recipes?
----------

Penn State currently has over 100 recipes for commonly used software. Unfortunately the recipes include many organization specific customizations, file paths and naming conventions. We are in the process of cleaning them up to share as well as adding support ways to make additional organization specific overrides.

You can find example recipes under the "Examples" directory. If you'd like to work with us on getting a recipe for a specific piece of software or have any suggestions for making bigfix recipes easier to share please open an issue or send us an email at clcmac@psu.edu.

Known Issues
----------

- AutoPkgBESEngine only supports the generation of a single prefetch item, but additional prefetch lines can be hardcoded into the recipes.

- BESUloader requires a master operator account. Please vote for this IBM RFE - http://www.ibm.com/developerworks/rfe/execute?use_case=viewRfe&CR_ID=41378

- BESRelevanceProvider only supports a single relevance statement and stores the return value in a statically named variable.


License
----------

Copyright The Pennsylvania State University.