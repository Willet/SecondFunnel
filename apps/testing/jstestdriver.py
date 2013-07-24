import subprocess
import os
import re
import shutil

from secondfunnel.settings.common import fromProjectRoot
from apps.testing.settings import GENERIC_BROWSER_LIST, ADDITIONAL_BROWSER_LIST, CONFIGS
from apps.testing.utils import parse_results


def getPath(path):
    """
    Returns the full path to the specified file or directory.

    @return: string
    """
    return fromProjectRoot(
        os.path.join("apps/testing", path)
    )


def startServer( browsers ):
    """
    Captures the browsers to be used for the JsTestDriver.

    @param browsers: The browser(s) to use if any.
    @return: None
    """
    applications = []
    browser_list = GENERIC_BROWSER_LIST + ADDITIONAL_BROWSER_LIST
    command = "java -jar {0} --port 9876".format(getPath("resources/JsTestDriver.jar"))
    
    for browser in browsers:
        script = [ b for b in browser_list if b == browser or re.match(r'' + browser + '($|/)', b) ] 
        app = browser if os.path.exists(browser) else None

        if not app and len(script) > 0:
            app = script[0]
        else:
            app = browser

        applications.append(app)

    if len(applications) > 0:
        # Determine if we were given an application of a full path
        # If given the full path to a browser, use the browser as it.
        script, scripts = getPath("scripts/browsers.sh"), []
        command += " --browser \""
        for application in applications:
            if os.path.exists(application):
                scripts.append("{0};%s".format(re.escape(application)))
            else:
                new_script = "/tmp/browsers-{0}.sh".format(re.escape(application))
                os.system("cp {0} {1}".format(script, new_script))
                scripts.append("{0};%s;{1}".format(new_script, re.escape(application)))
        command += ",".join(scripts) + "\""

    server = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    
    if len(browsers) == 0:
        phantom = subprocess.Popen("phantomjs {0}".format(getPath("resources/phantomjs-jstd.js")), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    return None


def call_JsTestDriver(config, tests, browsers, *args, **kwargs):
    """
    Calls the JsTestDriver with the specified arguments and options.

    @param config: The configuration file to use
    @param tests: List of individual tests to run if any.
    @param browsers: The path to the browsers to use (if any).
    @param args: Tuple of parameters.
    @param kwargs: Dictionary of remaining parameters.
    @return: None
    """
    command = "java -jar {0}".format(getPath("resources/JsTestDriver.jar"))
    basepath = os.path.abspath(
                   os.path.join(
                       fromProjectRoot('manage.py'), os.pardir))

    # Find the configuration file we're using.
    if config in CONFIGS:
        command += " --config {0}".format(getPath(CONFIGS[config]))
    else:
        config = getPath(config)
        if os.path.exists(config):
            command += " --config {0}".format(config)
        else:
            raise IOError("Specified file does not exist", config)

    command += " --runnerMode {0} --basePath {1} --tests {2} {3}".format(kwargs['mode'], basepath, tests, "--captureConsole" if kwargs['log'] else "")
    shutil.rmtree(getPath("tests/results"), ignore_errors=True)
    os.mkdir(getPath("tests/results"))
    command += " --testOutput apps/testing/tests/results > /dev/null"

    if not kwargs['remote']:
        startServer(browsers)

    import time
    time.sleep(5)
    
    testRunner = subprocess.Popen(command, shell=True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
    (out, err) = testRunner.communicate()

    if len(browsers) == 0:
        subprocess.Popen("killall - phantomjs", shell=True)
    
    subprocess.Popen("{0}".format(getPath("scripts/shutdown.sh")), shell=True)

    if err:
        raise RuntimeError(err)

    verbosity = int(kwargs['verbosity'])
    if verbosity > 0:
        data, output = parse_results(), ""
        for type, results in data.iteritems():
            print "%s (%d tests): \n"%(type, results['total'])
            for suite, cases in results['suites'].iteritems():
                print "%sSuite: %s:"%(" " * 2, suite)
                for case in cases:
                    print "%sTest: %s"%(" " * 6, case['name'])
                    if len(case['msg']) > 0:
                        print "%sMessage: %s"%(" " * 10, case['msg'])
                print

    return None

