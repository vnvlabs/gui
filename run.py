# -*- encoding: utf-8 -*-
import argparse
import os
import sys

from app import create_app
from app.base.blueprints.xterm import socketio
from theia import launch_theia


class MyConfig:
    DEBUG = False
    LOCAL = False
    basedir = os.path.abspath(os.path.dirname(__file__))
    auth = False
    port = 5001
    HOST = "0.0.0.0"
    DEFAULT_DATA_PREFIX = "../build/"
    LOGOUT_COOKIE = "vnvnginxcode"

    THEIA = 0
    THEIA_PORT = 5002
    THEIA_DIR=""
    NODE_EXE=""

    PARAVIEW = 0
    PARAVIEW_DIR=""
    PARAVIEW_SESSION_PORT_START=5003
    PARAVIEW_SESSION_PORT_END=5100
    PARAVIEW_DATA_DIR="/"

    NGINX_ADDRESS= "localhost"
    NGINX_PORT=4001

parser = argparse.ArgumentParser()
parser.add_argument("--port", help="port to run on (default 5001)")
parser.add_argument("--host", help="host to run on (default localhost)")
parser.add_argument("--paraview", help="directory containing paraview")
parser.add_argument("--theia", help="directory containing theia")
parser.add_argument("--node", help="path to node exe to use when running theia")
parser.add_argument("--profile", help="profile for debugging")

args, unknown = parser.parse_known_args()

if args.port:
    MyConfig.port = args.port

if args.host:
    MyConfig.HOST = args.host

if args.paraview:
    MyConfig.PARAVIEW = 1
    MyConfig.PARAVIEW_DIR = args.paraview

if args.theia:
    MyConfig.THEIA = 1
    MyConfig.THEIA_DIR = args.theia

if args.node:
    MyConfig.NODE_EXE = args.node

if args.profile == "ben":
    MyConfig.THEIA=1
    MyConfig.THEIA_DIR="/home/ben/source/vnvlabs.com/vnvlabs/gui/theia"
    MyConfig.NODE_EXE="/home/ben/.nvm/versions/node/v20.2.0/bin/node"
    MyConfig.PARAVIEW = 1
    MyConfig.PARAVIEW_DIR="/home/ben/source/vnvlabs.com/vnvlabs/gui/scripts/ParaView-5.10.1-osmesa-MPI-Linux-Python3.9-x86_64"

if __name__ == "__main__":

    app_config = MyConfig()
    app = create_app(app_config)
    if app_config.THEIA == 1:
        launch_theia(app_config.THEIA_DIR, os.getcwd(), app_config.HOST, app_config.THEIA_PORT, node=app_config.NODE_EXE)

    socketio.run(app,use_reloader=False, host=app_config.HOST, port=app_config.port)
