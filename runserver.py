#!/usr/bin/env python
"""
Utility script.  Since there's several applications that also need to be run
in tandam with our server beginning (and it's a bit hectic), this script makes
it easy to start the HTTP server, the HTTPS serer or stop them.
"""
import os
import shutil
import re
import shlex
import getpass
from subprocess import Popen, PIPE, STDOUT, call
try:
    from ordereddict import OrderedDict
except ImportError:
    from collections import OrderedDict


SERVICES = OrderedDict((
    ('rabbitmq-server', {
    	    'start': "echo \"{0}\" | sudo -S rabbitmq-server > log/rabbitmq.log 2>&1 &",
	    'stop': "echo \"{0}\" | sudo -S rabbitmqctl stop > /dev/null"
        }
    ),
    ('memcached', {
	    'start': "memcached -vv > log/memcached.log 2>&1 &",
        }
    ),
    ('manage.py runserver', {
	    'start': "python manage.py runserver > log/server.log 2>&1 &",
        }
    ),
    ('celeryd worker', {
	    'start': "python manage.py celeryd worker --loglevel=info > log/celery.log 2>&1 &",
        }
    ),
    ('stunnel', {
        }
    ),
))


HTTPS = {
    'cert': "stunnel/server.crt",
    'key': "stunnel/server.key",
    'config': "stunnel/dev_https"
}


def is_running( process ):
    """
    Determine if a process is running or not.

    @param process: The process name.
    @return: list or None
    """
    cmd = "ps ax | grep \"{0}\" | grep -v grep | awk '{{print $1}}'"
    p = Popen(cmd.format(process), shell=True, stdout=PIPE, stderr=STDOUT)
    (pid, err) = p.communicate()
    pids = []

    try:
        for p in re.findall(r'(\d+)+', pid):
            pids.append(int(p))
    except Exception, e:
        pids = None

    return pids


def start(password, https = False, ):
    """
    Starts the HTTP/HTTPS server on the dev environment.
    Reference: http://stackoverflow.com/questions/8023126

    @param password: Password needed for elevated privelege services.
    @param https: Whether to start the HTTPS server as well.
    @return: None
    """
    global SERVICES

    if https:
        if not os.path.exists("stunnel"):
            os.mkdir("stunnel")

        for key, path in HTTPS.iteritems():
            if not os.path.exists(path):
                setup()
                break

        
        https_services = [
            ('stunnel', {
                    'start': "rm log/stunnel.log > /dev/null 2>&1 && stunnel stunnel/dev_https > /dev/null 2>&1 &"
                }
            ),
            ('manage.py runserver 8003', {
                    'start': "HTTPS=on python manage.py runserver 8003 > log/https.log 2>&1 &"
                 }
            )
        ]

        runserver = SERVICES['manage.py runserver']['start']
        SERVICES['manage.py runserver']['start'] = "{0} {1}".format("DEVHTTPS=on", runserver)
        SERVICES = OrderedDict(SERVICES.items() + https_services)

    if not os.environ.get("VIRTUAL_ENV"):
        cmds = [ "source /usr/local/bin/virtualenvwrapper.sh", "workon SecondFunnel" ]
        for cmd in cmds:
            p = Popen(shlex.split(cmd))
            p.wait()
            stderr = p.stderr
	
            if stderr:
                raise Exception(stderr)

    if not os.path.exists("log"):
        os.mkdir("log")

    count = 0
    for process, commands in SERVICES.iteritems():
        pids = is_running(process)

        if pids:
            continue

        if 'start' in commands:
            count += 1
            call(commands['start'].format(password), shell=True)

    if count > 0:
        print "Started the services."
    else:
        print "Start server called, but nothing happened."

    return None


def stop(password):
    """
    Stops the running server processes.
    
    @param password: Password needed for elevated privelege services.
    @return: None
    """
    count = 0

    for process, commands in SERVICES.iteritems():
        pids = is_running(process)

        if not pids:
            continue

        if 'stop' in commands:
            count += 1
            call(commands['stop'].format(password), shell=True)
        else:
            count += 1
            for pid in pids:
                os.kill(pid, 15)

    if count > 0:
        print "Stopped the services."
    else:
        print "Stop server called, but nothing happened."

    return None


def restart(password, https = None):
    """
    Convenience method for restarting the services.

    @param password: Password needed for elevated privelege services.
    @param https: Boolean indicating whether to restart with HTTPS
    @return: None
    """
    import StringIO

    stdout, sys.stdout = sys.stdout, StringIO.StringIO()
    stop(password)
    start(password, https)
    sys.stdout, stdout = stdout, sys.stdout

    contents = stdout.getvalue()
    stdout.close()

    if "Started" in contents or "Stopped" in contents:
        print "Restarted the services."
    else:
        print "Restart server called, but nothing happened."

    return None


def setup():
    """
    Sets up the required files for the HTTPS service to run on the
    local development environment.

    @return: None
    """
    info = r"CA\nOntario\nKitchener\nWillet Inc\nDev\nlocalhost:8002\n\n\n\n"
    configfile = "pid=\n\ncert = stunnel/server.crt\nkey = stunnel/server.key\nsslVersion = SSLv3\nforeground = yes\ndebug = 7\noutput = log/stunnel.log\n\n[https]\naccept = 8002\nconnect = 8003\nTIMEOUTclose = 1\n"

    os.chdir("stunnel")
    Popen("openssl genrsa -out server.key 1024", shell=True, stdout=PIPE, stderr=STDOUT).wait()
    Popen("echo \"{0}\" | openssl req -new -key server.key -out server.csr".format(info), shell=True, stdout=PIPE, stderr=STDOUT)
    shutil.copy("server.key", "server.key.org")
    Popen("openssl rsa -in server.key.org -out server.key", shell=True, stdout=PIPE, stderr=STDOUT).wait()
    Popen("openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt", shell=True, stdout=PIPE, stderr=STDOUT).wait()

    with open("dev_https", 'w') as output:
        output.write(configfile)

    os.chdir(os.path.expanduser(os.path.expandvars("..")))
    return None


def arg_switch(option, opt_str, value, parser):
    """
    Helper function for switching the command that is to be run.

    @param option: The option instance.
    @param opt_str: Option string on the command-line.
    @param value: Arguments on the command-line.
    @param parser: The OptionParser instance
    @return: None
    """
    assert getattr(parser.values, option.dest) is None
    setattr(parser.values, option.dest, opt_str[2:])


if __name__ == "__main__":
    from optparse import OptionParser, make_option, OptionGroup
    import sys

    parser = OptionParser(usage="runserver.py [start [https] | stop]")

    # Prepocessing input
    keywords = ("start", "stop", "restart")
    arguments = ["--" + keyword if keyword in keywords else keyword for keyword in sys.argv[1:]]

    # Add options
    parser.add_option("--start", dest="cmd", default=None, action="callback", callback=arg_switch,
                      help="Start the HTTP/HTTPS server services.")
    parser.add_option("--stop", dest="cmd", default=None, action="callback", callback=arg_switch,
                      help="Stop the running server services.")
    parser.add_option("--restart", dest="cmd", default=None, action="callback", callback=arg_switch,
                      help="Restart the server services.")

    (options, args) = parser.parse_args(arguments)
    
    if options.cmd in ("restart", "start"):
        if len(args) > 1:
            parser.error("%s: Expects zero or one argument."%options.cmd)
        elif len(args) == 1 and not args[0] == "https":
            parser.error("%s: Unexpected argument: %s"%(args[0], options.cmd))
    elif options.cmd == "stop" and len(args) > 0:
        parser.error("%s: Expects no arguments"%options.cmd)

    d = dict(globals())
    password = getpass.getpass("Enter password: ")
    args = [password] + list(args)
    d[options.cmd](*args)
