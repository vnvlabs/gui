# -*- encoding: utf-8 -*-
import argparse
import os
import sys

from app import create_app
from app.base.blueprints.xterm import socketio
from theia import launch_theia


class MyConfig:
    NGINX_ADDRESS=None
    NGINX_SECURE=False

    DEBUG = False
    LOCAL = False
    basedir = os.path.abspath(os.path.dirname(__file__))
    auth = False
    port = 5000
    HOST = "0.0.0.0"
    DEFAULT_DATA_PREFIX = "../build/"
    LOGOUT_COOKIE = "vnvnginxcode"

    THEIA = 0
    THEIA_PORT = 5001
    THEIA_DIR=""
    NODE_EXE=""

    PARAVIEW = 0
    PARAVIEW_DIR=""
    PARAVIEW_SESSION_PORT_START=5003
    PARAVIEW_SESSION_PORT_END=5100
    PARAVIEW_DATA_DIR="/"



parser = argparse.ArgumentParser()
parser.add_argument("--profile", help="profile for debugging", default="default")

parser.add_argument("--nginx", help="host address")
parser.add_argument("--nginx_secure", type=bool, help="host address is https", default=False)



args, unknown = parser.parse_known_args()

if args.profile == "ben":

    MyConfig.THEIA=1
    MyConfig.THEIA_DIR="/home/ben/source/vnvlabs.com/vnvlabs/gui/theia"
    MyConfig.NODE_EXE="/home/ben/.nvm/versions/node/v20.2.0/bin/node"
    MyConfig.PARAVIEW = 1
    MyConfig.PARAVIEW_DIR="/home/ben/source/vnvlabs.com/vnvlabs/gui/scripts/ParaView-5.10.1-osmesa-MPI-Linux-Python3.9-x86_64"

elif args.profile == "docker":

    MyConfig.port = 5000
    MyConfig.THEIA = 1
    MyConfig.THEIA_PORT = 5001
    MyConfig.THEIA_DIR="/gui/theia"
    MyConfig.NODE_EXE="/versions/node/v20.2.0/bin/node"
    MyConfig.PARAVIEW = 1
    MyConfig.PARAVIEW_DIR="/gui/scripts/paraview"
    MyConfig.PARAVIEW_SESSION_PORT_START=5002
    MyConfig.PARAVIEW_SESSION_PORT_END = 5100

    if args.nginx:
        MyConfig.NGINX_ADDRESS = args.nginx
        MyConfig.NGINX_PROTO = args.nginx_secure




if __name__ == "__main__":

    app_config = MyConfig()
    app = create_app(app_config)
    if app_config.THEIA == 1:
        launch_theia(app_config.THEIA_DIR, os.getcwd(), app_config.HOST, app_config.THEIA_PORT, node=app_config.NODE_EXE)

    socketio.run(app, debug=False, host=app_config.HOST, port=app_config.port)
