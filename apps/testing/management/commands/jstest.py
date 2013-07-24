from django.core.management.base import BaseCommand, CommandError

from apps.testing.jstestdriver import call_JsTestDriver
from apps.testing.utils import install
 
from optparse import OptionParser, make_option


# Since we're using Python 2.6 instead of 2.7+
# http://docs.python.org/2/library/optparse.html#callback-example-6-variable-arguments
def vararg_callback(option, opt_str, value, parser):
    """
    Callback to allow variable arguments on the commandline.

    @param option: The corresponding option object
    @param opt_str: The string as seen on the command line
    @param value: A single argument or tuple of arguments parsed from the commandline
    @param parser: The OptionParser object
    """
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


def quieter(option, opt_str, value, parser):
    """
    Callback to make output less verbose.
    
    @param option: The corresponding option object
    @param opt_str: The string as seen on the command line
    @param value: A single argument or tuple of arguments parsed from the commandline
    @param parser: The OptionParser object
    """
    verbosity = int(getattr(parser.values, 'verbosity'))
    setattr(parser.values, 'verbosity', verbosity - 1)


class Command(BaseCommand):
    """
    Command class for the JavaScript tester; acts as an interface to simplify calling the associated
    program.

    @ivar args: A general overview of what arguments are accepted.
    @ivar help: The help message to display.
    @ivar option_list: Options accepted by this command.
    @ivar jstestdriver_option_list: List of options accepted by the JsTestDriver
    """
    help = 'Run JavaScript tests against the JsTestDriver/Jasmine setup.'
    
    option_list = BaseCommand.option_list + (
        make_option('-c', '--config', nargs=1, dest='config', default='desktop', help='Specify the config file to use (default: dev).'),
        make_option('-t', '--tests', dest='tests', default="all", help='Specify specific tests specified by regex to run or "all" to run all (default: all).'),
        make_option('-b', '--browsers', dest='browsers', default=[], help='Name of browsers to use for testing (default: headless webdriver).',
                    action="callback", callback=vararg_callback),
        make_option('-r', '--remote', action="store_true", dest='remote', default=False, help='Specify whether connecting to a remote server or not (default: False).'),
        make_option('-m', '--runner-mode', dest='mode', default="QUIET", help='Specify the runner mode to use; QUIET or DEBUG (default: QUIET)'),
        make_option('-l', '--log', dest='log', default=False, help="Capture responses/results in the console."),
        make_option('-q', '--quiet', nargs=0, help="Only print results, no names", action='callback', callback=quieter), 
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
            if len(args) > 0:
                self.print_help("./manage.py jstest", "")
                exit(1)
            else:
                call_JsTestDriver(**options)
        except IOError, (msg, filename):
            raise Exception("IOError, %s: %s"%(msg, filename))
        except RuntimeError, err:
            raise Exception(err)
