import json
import os
from python_api.build import VnVReader

THISDIR = os.path.dirname(os.path.abspath(__file__))

FILES = {}

def Read(filename, reader, config={}):
    return VnVReader.Read(filename, reader, json.dumps(config))
