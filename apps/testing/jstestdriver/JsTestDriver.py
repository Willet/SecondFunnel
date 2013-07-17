import subprocess, os, re
from secondfunnel.settings.common import fromProjectRoot


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



def capture( command, browsers ):
    """
    Captures the browsers to be used for the JsTestDriver.

    @param command: The initial base command used for this.
    @param browsers: The browser(s) to use if any.
    @return: None
    """
    processes, commands, browserpaths = [], [], []
    command += " --port 9876 --captureConsole"
    

    if len(browsers) == 0:
        commands += [ command,
                      "phantomjs {0} > /dev/null 2>&1".format(getPath("phantomjs/phantomjs-jstd.js")) ]
    else:
        # Find the path to the specified browsers.
        # Ignore IE for now, that's a different problem.
        # TODO: Internet Explorer Support
        browser_list = ( "google chrome", "chrome", "firefox", "safari" )
        command += " --browser "
        for browser in browsers:
            path = None
            if browser.lower() not in browser_list:
                raise Exception("ERROR: Unknown browser, {0}, specified.".format(browser))
            else:
                if browser == "chrome":
                    # Since chrome is shorthand for Google Chrome
                    browser = "google chrome"

                if browser.lower() == "safari":
                    # We have to do a workaround for safari to work
                    path = lambda: getPath("scripts/safari.sh")
                else:
                    path = lambda: getExePath(browser)
                
                # Check if we were passed a path, in which case we don't have to search!
                if os.path.exists(browser):
                    browserpaths.append(browser)
                else:
                    browserpaths.append(path())

        command += ",".join(browserpaths)
        commands += [ command ]
        browserpaths = [ path if path.find("safari.sh") == -1 else getExePath("Safari") for path in browserpaths ]

    for c in commands:
        processes.append(subprocess.Popen(c, shell=True, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT))
        
    return processes, browserpaths
    
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
    CONFIGS = {
        # Relative paths to the config files
        "sample": "sample/sample.conf",
        "dev": "jstestdriver/dev.conf"
    }

    basecommand = "java -jar {0}".format(getPath("jstestdriver/JsTestDriver-1.3.5.jar"))
    command = basecommand
    basepath = os.path.abspath(
                   os.path.join(
                       fromProjectRoot('manage.py'), os.pardir))
    command += " --runnerMode QUIET --basePath {0} --tests {1}".format(basepath, tests)
    
    if conf in CONFIGS:
        command += " --config {0}".format(getPath(CONFIGS[conf]))
    else:
        # Try to find the config file
        conf = getPath(conf)
        if os.path.exists(conf):
            command += " --config {0}".format(conf)
        else:
            raise Exception("ERROR: Specified config file, {0}, doesn't exist.".format(conf))

    if not commandline:
        command += " --testOutput apps/testing/jstest"

    # Make the calls
    print "Starting testing server...",
    processes, browsers = capture(basecommand, browsers)
    print "STARTED"
    print "Beginning Testing...."
    
    # This is really sloppy....
    import time
    time.sleep(10)
    os.system(command)

    # Terminate running processes
    for process in processes:
        process.kill()

    # Stop the started browsers.
    for browser in (browsers if len(browsers) > 0 else ["phantomjs"]):
        os.system("killall - {0}".format(re.split(r"[/\\]", browser)[-1]))

    # TODO: DETERMINE WAY TO DISPLAY XML RESULTS IN BROWSER W/ DJANGO
