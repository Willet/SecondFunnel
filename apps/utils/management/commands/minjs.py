# minjs.py - Minimize JS
# author: Ford Peprah
# minjs.py is a script that takes care of minimizing JS and bomining the JS files into one
# this reduces the number of external javascript scripts to reduce the number of HTTP requests, as well
# as reduces the size of the page call by eliminating whitespace and whatnot.  Makes use of Google's
# Closure Compiler.
import subprocess, os, re
from optparse import make_option

from django.core.management.base import NoArgsCommand, CommandError

GOOGLECLOSURE='compiler.jar' # where are google closure is
LANGUAGE='ECMASCRIPT5' # the level of browser we expect to be interacting with

# TO-DO: Abstract these out
PINPOINT_URL = 'apps/pinpoint/static/pinpoint/js/'
SECONDFUNNEL_URL = 'secondfunnel/static/js/'
TEMPLATE_URL = 'apps/pinpoint/templates/pinpoint/'

def buildpath( url, lst ):
    return map(lambda x: url + x, lst)

RESOURCES = [ 
    {'template': TEMPLATE_URL + 'campaign_scripts_desktop.html', 'production': SECONDFUNNEL_URL + 'willet-desktop.min.js',
     'development': buildpath(PINPOINT_URL,['pages.js']) + buildpath(SECONDFUNNEL_URL, ['jquery.viewport.js', 'jquery.masonry.min.js', 'jquery.masonry.prototypes.js', 
                                                                                        'jquery.imagesloaded.min.js', 'mason-bricks.js', 'loadfunction.js'])},
    {'template': TEMPLATE_URL + 'campaign_scripts_core.html', 'production': SECONDFUNNEL_URL + 'willet-core.min.js', 
     'development': buildpath(SECONDFUNNEL_URL, ['jquery-1.8.1.js', 'underscore.js']) + buildpath(PINPOINT_URL, ['utils.js', 'tracking.js'])},
    {'template': TEMPLATE_URL + 'campaign_scripts_mobile.html', 'production': SECONDFUNNEL_URL + 'willet-mobile.min.js',
     'development': buildpath(PINPOINT_URL,['pages.js']) + buildpath(SECONDFUNNEL_URL, ['loadfunction-mobile.js', 'mbp.js', 'jquery.mobile-1.2.1.js', 'swipe.js'])}
    ]

PATTERN = '<script src="\{% static "(.*)" %\}"></script>'


class Command(NoArgsCommand):
    """inherits from a NoArgsCommand; included command line arguments for use with production or development."""
    help = 'Minimizes the JS files that are available to be minimized and combines them appropriately.'

    option_list = NoArgsCommand.option_list + (
        make_option('-p', '--production', action='store_true', dest='production', default=False, help='Minimize the JS files and update campaign html to reflect changes.'),
        make_option('-d', '--development', action='store_true', dest='development', default=False, help='Update campaign to use un-minimized versions of JS'), )


    def handle_noargs(self, **options):
        count, globalcount = 0, 0
        if options['development']:
            #if we are developing, we must switch the campaign script html to use the unminified/unconcatenated versions
            #of the JS files
            for i in xrange(0, len(RESOURCES)):
                CAMPAIGN = RESOURCES[i]['template']
                data = ''
                with open(CAMPAIGN, 'r') as inputfile:
                    #open the file and adjust the appropriate lines
                    for line in inputfile:
                        if re.match(PATTERN, line.rstrip()) and "min.js" in line and "willet" in line:
                            count += 1
                            for newfile in RESOURCES[i]['development']:
                                data += PATTERN.replace("(.*)", newfile.replace(re.match('(.*)/static/', newfile).group(0), '')).replace('\\', "") + "\n"
                        else: data += line
                if count > 0:
                    #only update if we've actually made changes to the file
                    globalcount += 1
                    with open(CAMPAIGN, 'w') as outputfile: outputfile.writelines(data)
            print "Using unminimized files. (%d files changed)"%(globalcount)
        elif options['production']:
            #if we are pushing to production, we want to use the minified versions of the JS files, so we update the
            #campaign scripts accordingly.
            for i in xrange(0, len(RESOURCES)):
                CAMPAIGN = RESOURCES[i]['template']
                data, changes = '', 0
                with open(CAMPAIGN, 'r') as inputfile:
                    #open the file and adjust the appropriate lines
                    for line in inputfile:
                        PATTERNMATCH =  re.match(PATTERN, line.rstrip())
                        if PATTERNMATCH and ("apps/pinpoint/static/" + PATTERNMATCH.group(1) in RESOURCES[i]['development'] or 
                                             "secondfunnel/static/" + PATTERNMATCH.group(1) in RESOURCES[i]['development']):
                            count += 1
                        else:
                            if count > 0:
                                changes += 1
                                count = 0
                                newfile = RESOURCES[i]['production']
                                data += PATTERN.replace("(.*)", newfile.replace(re.match('(.*)/static/', newfile).group(0), '')).replace('\\', "") + "\n"
                            data += line
                if changes > 0: 
                    #once again, only update if we've actually made changes to files
                    globalcount += 1 
                    with open(CAMPAIGN, 'w') as outputfile:
                        outputfile.writelines(data)
            print "Using minimized files. (%d files changed)"%(globalcount)
        if not(options['development']):
            #As long as it's not the development, lets update the minified files
            for SET in [ (x['development'], x['production']) for x in RESOURCES ]:
                #for each SET of input and output, we want to generate the appropriate command and run it
                COMMAND = ['java', '-jar', GOOGLECLOSURE, '--language_in', LANGUAGE]
                for inputfile in SET[0]:
                    COMMAND += ['--js', inputfile.rstrip()]
                COMMAND += ['--js_output_file', SET[1].rstrip()]
                try:
                    p = subprocess.call(COMMAND)
                    if not(p == 0):
                        # It shouldn't fail, but it's possible.
                        print "Failed."
                        exit(1)
                except Exception as e:
                    print e
                    exit(2)
            print "Completed."
