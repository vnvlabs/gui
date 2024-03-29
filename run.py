# -*- encoding: utf-8 -*-
import argparse
import os
import sys
from app import create_app

import sys


class Config:
    DEBUG = True
    LOCAL = False
    basedir = os.path.abspath(os.path.dirname(__file__))
    passw = "password"
    auth = False
    port = 5001
    host = "0.0.0.0"
    DEFAULT_DATA_PREFIX = "../build/"
    THEIA_URL = "/theia"
    PARAVIEW_URL = "/paraview"
    LOGOUT_COOKIE = "vnvnginxcode"
    INPUTTABS_BROWSER = True
    INPUTTABS_PSIP = True
    INPUTTABS_ISSUES = True


parser = argparse.ArgumentParser()
parser.add_argument("--port", help="port to run on (default 5001)")
parser.add_argument("--host", help="host to run on (default localhost)")
parser.add_argument("--logout", help="name of logout cookie")
parser.add_argument("--theiapath", type=str, help="Theia Path")

args, unknown = parser.parse_known_args()

if args.theiapath:
    Config.THEIA_URL = args.theiapath

if args.port:
    Config.port = args.port

if args.host:
    Config.host = args.host

if args.logout:
    Config.LOGOUT_COOKIE = args.logout

if __name__ == "__main__":
    app_config = Config()
    app = create_app(app_config)
    app.run(use_reloader=False, host=app_config.host, port=app_config.port)
