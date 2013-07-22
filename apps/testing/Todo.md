#TODO

- Write tests

# DONE
- Support for modifying the configuration in Django
- Support for specifying browsers; can find path if not specified.
- Support for running specific tests, specified by regex
- Support for running non-headless
- Remove 3rd party libraries/tools from source control, have script prompt to download.
- Fix issue with browser processes.
- Fix firefox SIGTERM issue. (On MAC: type 'about:config', change 'resumefromcrash' to false, and 'crash report' to false), SHOULD be fixed in version 23.0
- Fix regex test matching error.  There is no regex, tests are in the form of testCase.testName (e.g. --tests A\ Suite)

# How to run individual tests
./manage.py jstest --tests testCase | testCase.testName | all
