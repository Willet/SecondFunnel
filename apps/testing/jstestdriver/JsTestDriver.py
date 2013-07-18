import subprocess, os, re

from secondfunnel.settings.common import fromProjectRoot
from apps.testing.jstestdriver.settings import GENERIC_BROWSER_LIST, ADDITIONAL_BROWSER_LIST, CONFIGS

def getPath(path):
    """
    Returns the full path to the specified file or directory.

    @return: string
    """
    return fromProjectRoot(
        os.path.join("apps/testing", path)
    )


def getExePath( exe ):
    """
    Returns the full path to the specified exe (executable) by finding the path
    using the environment $PATH variable.

    @param exe: The executable we're looking for.
    @return: String
    """
    import platform
    
    # Copy
    paths = [ path for path in os.environ['PATH'] ]
    path = None

    if platform.system() == "Darwin":
        # Need to add /Applications to the list of paths to search
        # on the MAC OS
        paths.append("/Applications")
    
    for path in paths:
        for (dirpath, dirnames, filenames) in os.walk(path, followlinks=True):
            for f in filenames:
                if f.lower() == exe.lower():
                    path = os.path.join(dirpath, f)
                    return path

    return path



def startServer( browsers ):
    """
    Captures the browsers to be used for the JsTestDriver.

    @param browsers: The browser(s) to use if any.
    @return: None
    """
    applications = []
    browser_list = GENERIC_BROWSER_LIST + ADDITIONAL_BROWSER_LIST

    # Find the path to the specified browsers.
    # TODO: Internet Explorer Support
    command = "java -jar {0} --port 9876".format(getPath("jstestdriver/JsTestDriver.jar"))
    
    for browser in browsers:
        script = [ b for b in browser_list if b == browser or re.match(r'' + browser + '($|/)', b) ] 
        app = browser if os.path.exists(browser) else None

        if not app and len(script) > 0:
            app = script[0]

        applications.append(app)
    
    if len(applications) > 0:
        script, scripts = getPath("scripts/browsers.sh"), []
        command += " --browser \""
        for application in applications:
            new_script = "/tmp/browsers-{0}.sh".format(re.escape(application))
            os.system("cp {0} {1}".format(script, new_script))
            scripts.append("{0};%s;{1}".format(new_script, re.escape(application)))
        command += ",".join(scripts) + "\""

    server = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    
    if len(browsers) == 0:
        phantom = subprocess.Popen("phantomjs {0}".format(getPath("phantomjs/phantomjs-jstd.js")), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    return None


def call_JsTestDriver(conf, tests, browsers, commandline, *args, **kwargs):
    """
    Calls the JsTestDriver with the specified arguments and options.

    @param conf: The configuration file to use
    @param tests: List of individual tests to run if any.
    @param browsers: The path to the browsers to use (if any).
    @param commandline: Whether or not to output to command-line or not.
    @param args: Tuple of parameters.
    @param kwargs: Dictionary of remaining parameters.
    @return: None
    """
    command = "java -jar {0}".format(getPath("jstestdriver/JsTestDriver.jar"))
    basepath = os.path.abspath(
                   os.path.join(
                       fromProjectRoot('manage.py'), os.pardir))

    if conf in CONFIGS:
        command += " --config {0}".format(getPath(CONFIGS[conf]))
    else:
        # Try to find the config file
        conf = getPath(conf)
        if os.path.exists(conf):
            command += " --config {0}".format(conf)
        else:
            raise Exception("ERROR: Specified config file, {0}, doesn't exist.".format(conf))

    command += " --runnerMode {0} --basePath {1} --tests {2}".format(kwargs['mode'], basepath, tests)

    if not commandline:
        command += " --testOutput apps/testing/jstest"

    # Make the calls
    print "Starting server....",
    if not kwargs['remote']:
        startServer(browsers)

    print "STARTED"
    print "Starting testing..."
    
    # Bit hacky for the time being...
    import time
    time.sleep(5)
    os.system(command)
    
    if len(browsers) == 0:
        os.system("killall - phantomjs")
    os.system("{0}".format(getPath("scripts/shutdown.sh")))

    # TODO: DETERMINE WAY TO DISPLAY XML RESULTS IN BROWSER W/ DJANGO
