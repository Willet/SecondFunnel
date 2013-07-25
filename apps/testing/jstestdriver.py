import subprocess
import os
import re
import shutil
import sys
import random

from secondfunnel.settings.common import fromProjectRoot
from apps.testing.settings import BROWSERS_MAC, BROWSERS_LINUX, CONFIGS
from apps.testing.utils import parse_results, getPath


TASKS = []


def wait_for_pid(application):
    """
    Waits until it can get the pid of the specified application.

    @param application: Name of the application to get the pid of
    @return: int
    """
    pid = None
    cmd = "ps -ax | grep \"{0}\" | grep -v grep | grep -v open | awk '{{print $1}}' | tail -n 1".format(application)
    while not pid or len(pid) == 0:
        pid = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        pid, err = pid.communicate()

        if err:
            raise Exception(err)
    
    return int(pid)


def capture_browser(url, browser, server):
    """
    """
    platform = sys.platform.lower()
    browsers = (BROWSERS_MAC if platform == "darwin" else BROWSERS_LINUX)
    
    for b in browsers:
        if browser in b.lower():
            browser = b
            break

    profileDir = ("~/Library/Application Support/Firefox" if platform == "darwin" else "~/.mozilla/firefox")
    application, args = None, ""
    paths = os.environ["PATH"].split(":")

    # Additional step for MAC OS since Application DIR is not on the path.
    if platform == "darwin":
        for (dirpath, dirnames, filenames) in os.walk("/Applications", followlinks=True):
            if '.app' in dirpath:
                paths.append(os.path.join(dirpath, "Contents/MacOS/"))
                del dirnames[:]

    for path in paths:
        symbolic_links = re.split(r'[\\/]', path)

        for i in range(0, len(symbolic_links)):
            app = os.path.join(os.path.join(os.sep, *symbolic_links[:i + 1]), browser)
            if os.path.isfile(app) and os.access(app, os.X_OK):
                application = app
                break

        if application:
            break

    if not application:
        application = browser

    # Firefox and Chrome require special additional instructions
    if "firefox" in browser.lower():
        tempProfile = "%d.JSTESTDRIVER"%(random.randint(0, sys.maxint))
        profilepath = os.path.join(os.path.expanduser(profileDir), "profiles.ini")
        with open(profilepath, 'r') as profile:
            if not os.path.exists("/tmp/profiles.ini"):
                with open("/tmp/profiles.ini", 'w') as cpy:
                    cpy.write("".join(profile.readlines()))
                    
            TASKS.append('rm -r "{0}"/Profiles/*.{1}'.format(os.path.expanduser(profileDir), tempProfile))
            TASKS.append('mv /tmp/profiles.ini \"{0}\"'.format(profilepath))
        args = "-p {0}".format(tempProfile)
        p = subprocess.Popen("{0} -CreateProfile {1}".format(application, tempProfile), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.wait()
    elif "chrome" in browser.lower():
        tempProfile = "/tmp/%d.GOOGLE.CHROME.PROFILE.JSTESTDRIVER"%(random.randint(0, sys.maxint))
        args = '--user-data-dir=\"{0}\" --no-first-run --no-default-browser-check'.format(tempProfile)

    # Safari can't be opened normally
    cmd = ("open -na {0} {1} -g {2}" if "safari" in browser.lower() else "\"{0}\" {1} {2} &").format(application, url, args)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    pid = wait_for_pid(application)
    TASKS.append("kill -TERM {0}".format(pid))

    # Wait until the browser is captured
    while True:
        line = server.stdout.readline()
        if 'Browser Captured' in line:
            break

    server.stdout.flush()

    return


def stop_server():
    """
    Shutdowns the server by running all the remaining tasks in the shell.

    @return: None
    """
    for task in TASKS[::-1]:
        t = subprocess.Popen(task, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        t.wait()

    for (path, dirs, files) in os.walk('/tmp/'):
        for dir in dirs:
            if 'JSTESTDRIVER' in dir:
                for (dirpath, dirnames, filenames) in os.walk(os.path.join(path, dir), topdown=False):
                    for filename in filenames:
                        os.remove(os.path.join(dirpath, filename))
                    shutil.rmtree(dirpath)

    return


def start_server( browsers ):
    """
    Captures the browsers to be used for the JsTestDriver.

    @param browsers: The browser(s) to use if any.
    @return: None
    """
    pid = None
    command = "nohup java -jar {0} --port 9876 --runnerMode INFO".format(getPath("resources/JsTestDriver.jar"))

    # Start the server
    server = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    pid = wait_for_pid("/usr/bin/java -jar .*/resources/JsTestDriver.jar")
    TASKS.append("kill {0}".format(pid))

    # Wait for the server to finish booting up
    while True:
        line = server.stdout.readline()
        if "Finished action run" in line:
            server.stdout.flush()
            break

    # If no browser(s) are specified, headless
    if len(browsers) == 0:
        phantom = subprocess.Popen("nohup phantomjs {0}".format(getPath("resources/phantomjs-jstd.js")), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        pid = wait_for_pid("phantomjs")
        TASKS.append("kill {0}".format(pid))

        # Wait for the capture to finish
        while True:
            line = phantom.stdout.readline()
            if "success" in line:
                break

    else:
        for browser in browsers:
            try:
                capture_browser("http://localhost:9876/capture", browser, server)
            except Exception as e:
                stop_server()
                raise Exception(e)

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

    if config in CONFIGS:
        command += " --config {0}".format(getPath(CONFIGS[config]))
    else:
        config = getPath(config)
        if os.path.exists(config):
            command += " --config {0}".format(config)
        else:
            raise IOError("Specified file does not exist", config)

    command += " --basePath {0} --tests {1} {2} --testOutput apps/testing/tests/results > /dev/null".format(basepath, tests, "--captureConsole" if kwargs['log'] else "")
    shutil.rmtree(getPath("tests/results"), ignore_errors=True)
    os.mkdir(getPath("tests/results"))

    if not kwargs['remote']:
        start_server(browsers)

    testRunner = subprocess.Popen(command, shell=True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
    (out, err) = testRunner.communicate()
    stop_server()

    if 'error' in out:
        raise RuntimeError(out)

    verbosity = int(kwargs['verbosity'])
    data, output = parse_results(), ""
    for type, results in data.iteritems():
        print "%s (%d tests): "%(type, results['total'])
        if verbosity > 0:
            for suite, cases in results['suites'].iteritems():
                print "%sSuite: %s:"%(" " * 2, suite)
                for case in cases:
                    print "%sTest: %s"%(" " * 6, case['name'])
                    if len(case['msg']) > 0:
                        print "%sMessage: %s"%(" " * 10, case['msg'])
                print

    return None
