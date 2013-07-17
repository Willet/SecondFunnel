#Testing Outline
----------------  
<br>
<br>
###Requirements
---------------
- Test Databases: e.g. creating and setting up a sample client.
- RequestFactories for creating *fake* requests in order to test the Python code and generated HTML.
- Jasmine/QUnit/JSTestDriver to test Javascript.
- Selenium to put it all together.

<br>

###[Jasmine](http://pivotal.github.io/jasmine/)
----------
**Benefits**
  
- Django library, 'django.js' to generate view for the Jasmine tests.
- Fairly simple and straightforward implementation.
- Able to specify fairly terse/involved test suites.
- Output of pass/fail with long description.
- Tests run really fast since they don't depend on the DOM.

**Cons**

- No native headless.
- Can't specify different browsers.
- No apparent remote testing functionality.
- Not coupled with DOM -> tests have to be updated as DOM is updated -> tests may not be relevant as HTML attributes / IDs / Classes are changed.
    
**Other**

- Third party libraries to provide functionality for integrating with jQuery.

<br>

###[QUnit](http://qunitjs.com/)
--------
**Benefits**

- Integration with JQuery (native support, used by the JQuery team!)
- Django library, 'django.js' to generate view for QUnit tests.
- Fairly simple to write and integrate tests.
- Support for IE6+/Chrome/Firefox/Safari/Opera
- Error message handling and well documented API.
- Bundled plugin for PhantomJS Runner to use headless.
- JUnit Logger plugin to produce XML (can be used with Jenkins).

**Cons**

- No native headless.
- Can't specify different browsers.
- No apparent remote testing functionality.

**Other**

- Third party library called 'django-qunit' that provides the ability to run QUnit alongside Django but hasn't been updated in 3 years, so...

<br>

###[JSTestDriver](https://code.google.com/p/js-test-driver/)
---------------
**Benefits**

- Support for testing in multiple browsers by specifying file paths to the binaries (particularly useful for IE testing and older browsers).
- Integration with QUnit.
- Native headless.
- Output results to CLI or file.
- Well documented API.

**Cons**

- No apparent remote testing capabilities.
- No native integration with Django.

**Other**

- N/A