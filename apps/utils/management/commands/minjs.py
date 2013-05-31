# minjs.py - Minimize JS
# author: Ford Peprah
# minjs.py is a script that takes care of minimizing JS and bomining the JS files into one
# this reduces the number of external javascript scripts to reduce the number of HTTP requests, as well
# as reduces the size of the page call by eliminating whitespace and whatnot.  Makes use of Google's
# Closure Compiler.
import subprocess, os, re, urllib, httplib
from optparse import make_option

from django.core.management.base import NoArgsCommand, CommandError


# TO-DO: Abstract these out
PINPOINT_URL = 'apps/pinpoint/static/pinpoint/js/'
SECONDFUNNEL_URL = 'secondfunnel/static/js/'
TEMPLATE_URL = 'apps/pinpoint/templates/pinpoint/'

def buildpath( url, lst ):
    return map(lambda x: url + x, lst)

RESOURCES = [ 
    {'production': SECONDFUNNEL_URL + 'willet-desktop.min.js',
     'development': buildpath(PINPOINT_URL,['pages.js']) + buildpath(SECONDFUNNEL_URL, ['jquery.viewport.js', 'jquery.masonry.min.js', 'jquery.masonry.prototypes.js', 
                                                                                        'jquery.imagesloaded.min.js', 'mason-bricks.js', 'loadfunction.js'])},
    {'production': SECONDFUNNEL_URL + 'willet-core.min.js', 
     'development': buildpath(SECONDFUNNEL_URL, ['underscore.js']) + buildpath(PINPOINT_URL, ['utils.js', 'tracking.js'])},
    {'production': SECONDFUNNEL_URL + 'willet-mobile.min.js',
     'development': buildpath(PINPOINT_URL,['pages.js']) + buildpath(SECONDFUNNEL_URL, ['loadfunction-mobile.js', 'mbp.js', 'jquery.mobile-1.2.1.js', 'swipe.js'])}
    ]


class Command(NoArgsCommand):
    """inherits from a NoArgsCommand; included command line arguments for use with production or development."""
    help = 'Minimizes the JS files that are available to be minimized and combines them appropriately.'
    option_list = NoArgsCommand.option_list
    # TO-DO FIX ISSUE W/ CREATING THE WILLET CORE MINIFIED JS FILE

    def minify(self, files, output):
        # Minifies the files by calling the UglifyJS HTTP API service
        url = "marijnhaverbeke.nl"
        # SETTINGS: DO NOT CHANGE
        sources = []
        for file in files: 
            with open(file, 'r') as source:
                js_code = ''
                for line in source.readlines():
                    js_code += line
                sources.append(('js_code', js_code))
        params = urllib.urlencode(sources)
        headers = { "Content-type": "application/x-www-form-urlencoded" }
        
        # Start connection and get the minified code 
        conn = httplib.HTTPConnection(url)
        conn.request('POST', "/uglifyjs", params, headers)
        data = conn.getresponse().read()
        with open(output, 'w') as result:
            result.writelines(data)

        return data

    def handle_noargs(self, **options):
        count, globalcount = 0, 0
        # IMPORTANT: NEED AN INTERNET CONNECTION TO WORK PROPERLY
        for SET in [ (x['development'], x['production']) for x in RESOURCES ]:
            try:
                save = self.minify(SET[0], SET[1])
            except Exception as e:
                print e
                exit(1)
            print "Successfully created minified file: %s"%(SET[1])
