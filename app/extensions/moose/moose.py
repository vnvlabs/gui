import json
import os.path
import subprocess

import pyhit

def extract_moose_schema(filename):
    a = subprocess.check_output([filename, "--json"], cwd=os.path.dirname(filename),timeout=10).decode('ascii')
    akey = "**START JSON DATA**"
    ekey = "**END JSON DATA**"
    start_pos = a.find(akey) + len(akey)
    end_pos = a.find(ekey)
    return json.loads(a[start_pos:end_pos])
def format(content):
    nodes = pyhit.parse(content)
    return nodes.format()

def getBlockAtPosition(row, col, pynode):
    for child in pynode.children:

def validate(content):
    nodes = pyhit.parse(content)

class MooseFile:
    def __init__(self, filename, application):
        dirname = os.path.dirname(filename)
        basname = os.path.basename(filename)
        abspath = os.path.abspath(filename)
        nodes = pyhit.load(abspath)
        schema = load_schema(application)
