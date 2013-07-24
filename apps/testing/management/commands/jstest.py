from django.core.management.base import BaseCommand, CommandError

from apps.testing.jstestdriver import call_JsTestDriver
 
from optparse import OptionParser, make_option


# Since we're using Python 2.6 instead of 2.7+
# http://docs.python.org/2/library/optparse.html#callback-example-6-variable-arguments
def vararg_callback(option, opt_str, value, parser):
    assert value is None
    value = []
    
    def floatable(str):
        try:
            float(str)
            return True
        except ValueError:
            return False
        
    for arg in parser.rargs:
        # stop on --foo like options
        if arg[:2] == "--" and len(arg) > 2:
            break
        # stop on -a, but not on -3 or -3.0
        if arg[:1] == "-" and len(arg) > 1 and not floatable(arg):
            break
        value.append(arg)

    del parser.rargs[:len(value)]
    setattr(parser.values, option.dest, value)


class Command(BaseCommand):
    """
    Command class for the JavaScript tester; acts as an interface to simplify calling the associated
    program.

    @ivar args: A general overview of what arguments are accepted.
    @ivar help: The help message to display.
    @ivar option_list: Options accepted by this command.
    @ivar jstestdriver_option_list: List of options accepted by the JsTestDriver
    """
    args = "[ [ -c|--config /path/to/configfile ] [ -t|--tests testSuite.testName | testSuite | .testName ] [ -b|--browsers browser1 ... browsern ] [ -d|--commandline ] \
            [ -l | --log ] ]"
    help = 'Run JavaScript tests against the JsTestDriver/Jasmine setup.'
    
    option_list = BaseCommand.option_list + (
        make_option('-c', '--config', nargs=1, dest='config', default='desktop', help='Specify the config file to use (default: dev).'),
        make_option('-t', '--tests', dest='tests', default="all", help='Specify specific tests specified by regex to run or "all" to run all (default: all).'),
        make_option('-b', '--browsers', dest='browsers', default=[], help='Name of browsers to use for testing (default: headless webdriver).',
                    action="callback", callback=vararg_callback),
        make_option('-d', '--commandline', action="store_false", dest='commandline', default=True, help='Output to command line or to browser (default: True).'),
        make_option('-r', '--remote', action="store_true", dest='remote', default=False, help='Specify whether connecting to a remote server or not (default: False).'),
        make_option('-m', '--runner-mode', dest='mode', default="QUIET", help='Specify the runner mode to use; QUIET or DEBUG (default: QUIET)'),
        make_option('-l', '--log', dest='log', default=False, help="Capture responses/results in the console."),
    )

    def handle(self, *args, **options):
        """
        Handles the execution of the JavaScript testing by calling the appropriate sub-program.

        @param self: The command being called.
        @param: A tuple of passed arguments.
        @param: A dict of arguments as specified by the option_list

        @return: None
        """
        try:
            call_JsTestDriver(**options)
        except Exception as e:
            raise Exception("Unrecognized command")
