# -*- encoding: utf-8 -*-
import argparse
import os
import sys

from app import create_app
from app.base.blueprints.files import load_default_file
from app.base.blueprints.xterm import socketio
from app.models.VnVFile import VnVFile
from app.models.VnVInputFile import VnVInputFile
from theia import launch_theia


class MyConfig:
    ADDRESS='0.0.0.0'
    SECURE=False
    NGINX=False

    HOME=os.environ.get("VNV_HOME_PATH",os.path.expanduser("~"))

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
    PARAVIEW_PORT = 5002
    PARAVIEW_SESSION_PORT_START=5003
    PARAVIEW_SESSION_PORT_END=5100
    PARAVIEW_DATA_DIR="/"

    DEFAULT_EXES = {}
    DEFAULT_REPORTS = {}


parser = argparse.ArgumentParser()
parser.add_argument("--profile", help="profile for debugging", default="default")

parser.add_argument("--address", help="host address", default='0.0.0.0')
parser.add_argument("--secure", type=bool, help="host address is https", default=False)
parser.add_argument("--nginx", type=bool, help="is this behind the nginx server", default=False)



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
    MyConfig.PARAVIEW_PORT=5002
    MyConfig.PARAVIEW_SESSION_PORT_START=5003
    MyConfig.PARAVIEW_SESSION_PORT_END = 5100

    MyConfig.DEFAULT_EXES = {"Moose Example 1" : {
        "path" : "/software/moose/examples/ex01_inputfile/ex01-opt",
        "defs" : {
            "args" : "-i ex01.i"}
        }
    }


MyConfig.ADDRESS = args.address
MyConfig.SECURE = args.secure
MyConfig.NGINX = args.nginx


def launch_paraview(PARAVIEW_DIR, port, HOST, home="/"):
    os.system(f"{PARAVIEW_DIR}/bin/pvpython -u -m paraview.apps.visualizer --port {port} --host {HOST} --data {home} --timeout 500000 &")



if __name__ == "__main__":

    app_config = MyConfig()
    app = create_app(app_config)

    for k,v in app_config.DEFAULT_EXES.items():
        if os.path.exists(v["path"]):
            VnVInputFile.add(k,v["path"],defs=v["defs"])

    for k, v in app_config.DEFAULT_REPORTS.items():
        load_default_file(k,v)

    if app_config.THEIA == 1:
        launch_theia(app_config.THEIA_DIR, os.getcwd(), app_config.HOST, app_config.THEIA_PORT, node=app_config.NODE_EXE, home=app_config.HOME)
    if app_config.PARAVIEW == 1:
        launch_paraview(app_config.PARAVIEW_DIR, app_config.PARAVIEW_PORT, app_config.HOST, home=app_config.HOME)

    socketio.run(app, debug=False, host=app_config.HOST, port=app_config.port)
