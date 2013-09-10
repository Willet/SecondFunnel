from apps.testing.settings import RESOURCES as resources
from secondfunnel.settings.common import from_project_root

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
import xml.etree.ElementTree as ET
import os
import json
import sys
import subprocess
import re



def parse_results():
    data = OrderedDict(zip(['Passed', 'Failed'], 
                           [{'total': 0, 'suites': {}}.copy() for i in range(0, 3)]))

    for (dirpath, dirname, filenames) in os.walk('apps/testing/tests/results'):
        for fname in filenames:
            if not extension(fname) == "xml":
                continue

            tree = ET.parse(os.path.join(dirpath, fname))
            root, suite = tree.getroot(), {}
            suitename = root.attrib['name']
            data['Failed']['total'] += int(root.attrib['failures']) + int(root.attrib['errors'])
            data['Passed']['total'] += int(root.attrib['tests']) - data['Failed']['total']
            
            for case in root.iter('testcase'):
                type, msg, children = 'Passed', "", case[:]
                
                for child in children:
                    if child.tag == 'failure':
                        type = "Failed"
                    else:
                        type = child.tag
                    msg = json.loads(child.attrib['message'])[0]['message']

                if suitename not in data[type]['suites']:
                    data[type]['suites'][suitename] = []

                data[type]['suites'][suitename].append({'name': case.attrib['name'], 'msg': msg})

    return data


def extension( filename ):
    """
    Return the extension of a file.

    @param filename: Name of the file.
    @return: String
    """
    return filename.split(".")[-1]


def getPath(path):
    """
    Returns the full path to the specified file or directory.

    @return: string
    """
    return from_project_root(
        os.path.join("apps/testing", path)
    )


def install():
    platform, downloader = sys.platform.lower(), None

    if platform == "darwin":
        downloader = "curl -L"
    elif platform == "linux":
        downloader = "wget"
    else:
        raise Exception("Unsupported Operating System")

    dir = os.getcwd()
    os.chdir(os.path.abspath(os.path.dirname(__file__)))

    if not os.path.exists("resources"):
        os.mkdir("resources")

    for resource, src in resources.iteritems():
        if not os.path.exists(resource):
            if extension(src) == "zip":
                filename = re.split(r'[\\/]', src)[-1]
                cmd = " ".join((downloader, src, "-o", filename))
                cmd += "&& unzip {0} -d {1} && rm {0}".format(filename, resource)
            else:
                cmd = " ".join((downloader, src, "-o", resource))
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            (stdout, stderr) = p.communicate()
            if stderr:
                raise Exception(stderr)

    os.chdir(dir)

    status = os.system("command -v phantomjs > /dev/null 2>&1")
    if not status == 0:
        if platform == "darwin":
            cmd = "brew install phantomjs"
        else:
            cmd = "sudo apt-get install phantomjs"
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (stdout, stderr) = p.communicate()
        if stderr:
            raise Exception(stderr)

    # Explicit return
    return None