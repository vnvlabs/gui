# -*- encoding: utf-8 -*-
import glob
import importlib
import json
import os
import shutil
import threading
import uuid

from flask import Blueprint, render_template, request, make_response, jsonify, send_file, current_app
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from werkzeug.utils import redirect
from pygments.lexers import get_lexer_by_name

from paraview import start_paraview_server, wait_for_paraview_to_start
from . import blueprints

from werkzeug.security import generate_password_hash, check_password_hash
from app.Directory import VNV_DIR_PATH
from .utils.utils import render_error


blueprint = Blueprint(
    'base',
    __name__,
    url_prefix='',
    template_folder='templates'
)


def config(conf):
    pass


CUSTOM_BLUEPRINTS = []


DEFAULT_SCHEMA = {
    "exclude_parent_blueprints" : "<bool - dont include any previously defined blueprints",
    "exclude_parent_executables" : "<bool - dont include any previously defined executables",
    "exclude_parent_reports" : "<bool - dont include any previously defined reports",
    "blueprints" : {
        "name" : "<directory containing a __init__.py file with the blueprint defined in it",
        "name1" : "<directory containing a __init__.py file with the blueprint defined in it",  
        "etc" : "for info on how to write a blueprint, see the psip example.", 
    },
    "executables" : {
       "name" : {"filename" : "<path to executable>" , "description" : "<string>", "package" : "<string>"},
       "name1" : {"filename" : "<path to executable>" , "description" : "<string>", "package" : "<string>"},  
       "etc" : {"filename" : "<path to executable>" , "description" : "<string>", "package" : "<string>"}
    },
    "reports" : {
        "name" : {"filename" : "<path to report file>" , "reader" : "reader used to read report", "description" : "<string>"},
        "name1" : {"filename" : "<path to report file>" , "reader" : "reader used to read report", "description" : "<string>"},
        "etc" : {"filename" : "<path to report file>" , "reader" : "reader used to read report", "description" : "<string>"}
    }
}

def load_blueprint(name, directory):
    temp_bp_dir = os.path.join(VNV_DIR_PATH, "temp", "blueprints", name)
    if os.path.exists(temp_bp_dir):
        shutil.rmtree(temp_bp_dir)

    print("Adding Additional module ", name)
    shutil.copytree(os.path.join(directory), temp_bp_dir, dirs_exist_ok=True)
    threading.Event().wait(1)
    ALL_BLUEPRINTS[name] = importlib.import_module("app.temp.blueprints." + name)
    blueprint.register_blueprint(ALL_BLUEPRINTS[name].blueprint)


def updateBranding(config, pd):
    
    if "blueprints" in config:
 
        if config.get("exclude_parent_blueprints", False):
               for k in CUSTOM_BLUEPRINTS:
                   ALL_BLUEPRINTS.pop(k)
            
        bp = config["blueprints"]
        for k, v in bp.items():
            temp_bp_dir = os.path.join(VNV_DIR_PATH, "temp", "blueprints", k)
            if os.path.exists(temp_bp_dir):
                shutil.rmtree(temp_bp_dir)

            print("Adding Additional module ", k)
            shutil.copytree(os.path.join(pd, v), temp_bp_dir, dirs_exist_ok=True)
            threading.Event().wait(1)
            ALL_BLUEPRINTS[k] = importlib.import_module("app.temp.blueprints." + k)
            CUSTOM_BLUEPRINTS.append(k)
            
    if blueprints.HAS_VNV:
        
        if config.get("exclude_parent_excutables", False):
            blueprints.inputfiles.vnv_executables = {}

        for key, value in config.get("executables", {}).items():
                        
            blueprints.inputfiles.vnv_executables[key] = {
                "filename" :  os.path.join(pd, os.path.expandvars(value["filename"])),
                "description" : value.get("description", "No Description Available"),
                "package" :  value.get("package", "VnV")
            }

        blueprints.files.load_defaults(config.get("reports", {}),  config.get("exclude_parent_reports", False))


FIRST_TIME = None
if FIRST_TIME is None:
    FIRST_TIME = False


    IMAGES_PATH = "/static/assets/images"
    IMAGES_DIR = os.path.join(VNV_DIR_PATH, IMAGES_PATH[1:])
    TEMPLATES_DIR = os.path.join(VNV_DIR_PATH, "base/templates")
    LOGO_SMALL = "logo.png"
    LOGO_LARGE = "logo.png"
    LOGO_ICON = "favicon.ico"
    COPYRIGHT_LINK = "mailto:boneill@rnet-tech.com"
    COPYRIGHT_MESSAGE = "RNET Technologies Inc. 2022"
    HOME_FILE = "includes/intro.html"
    TITLE_NAME = "VnV Toolkit"

    ALL_BLUEPRINTS = {}
    
    if blueprints.HAS_VNV:
        

        ALL_BLUEPRINTS = {
            "inputfiles": blueprints.inputfiles,
            "files": blueprints.files,
            "temp": blueprints.tempfiles,
            "help": blueprints.help,
            "directives": blueprints.directives,
            "xterm" : blueprints.xterm
            }

        try:
            ALL_BLUEPRINTS["moose"] = blueprints.plugins.moose
        except:
            print("Could not load moose")

        blueprints.inputfiles.vnv_executables["Custom"] = {
            "filename" : "",
            "description" : "Custom Path",
            "package" : ""   
        }

    
    

    #Load the users home registration file. 
    global_reg_file = os.path.expanduser("~/.vnv")
    try:
     with open(global_reg_file,'r') as f:
        reg = json.load(f)
        
        for package,filename in reg["gui"].items():
            try:  
                with open(filename,'r') as w:
                   updateBranding(json.load(w), os.path.dirname(filename))
            except Exception as e:
                print(e)
                print("Failed to load declared config file: ", filename )
    except:
        pass

    from app.base.blueprints import notifications
    from app.base.blueprints import browser
    ALL_BLUEPRINTS["notifications"] = notifications
    ALL_BLUEPRINTS["browser"] = browser
    
    for k, v in ALL_BLUEPRINTS.items():
        blueprint.register_blueprint(v.blueprint)



@blueprint.route("/ping")
def ping():
    return make_response("pong",200)


@blueprint.route('/paraview')
def paraview_route():

    if current_app.config["PARAVIEW"]:

        filename = request.args.get("file","")
        if len(filename) and os.path.exists(filename):
            uid, success = start_paraview_server(filename)
            autostop=10
        else:
            uid , success = start_paraview_server(None)
            autostop = 10000

        if uid is None:
            return render_error(200, "All available Paraview Ports are in use.", nohome=True)

        smurl = f"/paraview/session/{uid}"

        if "wrapper" in request.args:
            return render_template("paraview/wrapper.html",  sessionManagerUrl=smurl, success=True, autostop=autostop)

        return make_response(render_template('paraview/index.html', sessionManagerUrl=smurl, success=True, autostop=autostop) ,200)

    return render_error(200, "ParaviewVisualzier is not configured", nohome=True)



@blueprint.route("/paraview/session/<int:uid>", methods=["POST"])
def paraview_websocket(uid):

    if current_app.config["PARAVIEW"] == 0:
        return make_response(jsonify({"error": "paraview not configured"}), 200)

    wait_for_paraview_to_start(uid)

    address = current_app.config["ADDRESS"]
    p = "wss" if current_app.config["SECURE"] else "ws"
    nginx = current_app.config["NGINX"]

    if nginx:
            ws = f"{p}://{address}/ws/{uid}"
    else:
            ws = f"{p}://{address}:{uid}/ws"

    return make_response(jsonify({"sessionURL": ws}), 200)


@blueprint.route('/theia')
def theia_route():
    if current_app.config["THEIA"] == 1:

        address = current_app.config["ADDRESS"]
        p = "https" if current_app.config["SECURE"] else "http"
        nginx = current_app.config["NGINX"]


        if nginx:
            src=f"{p}://{address}/theia_redirect"
        else:
            src = f"{p}://{address}:{current_app.config['THEIA_PORT']}"

        if "wrapped" in request.args:
            return render_template("ide.html", src=src)
        else:
            return make_response(redirect(src), 302)

    return render_error(200, "Eclipse Theia is not configured", nohome=True)

@blueprint.route('/avatar/<username>')
def avatar_route(username):
    return send_file("static/assets/images/user/AVATARS.png")


@blueprint.route("icon")
def icon():
    p = request.args.get("package")
    return send_file("static/assets/images/close.png")


@blueprint.route("/")
def home():
    return redirect("/files/view"),302

def available_ports():
    return range(14000, 14010)


context_map = {
    "file": lambda x: glob.glob(x + "*"),
}


def getContext(context, prefix):
    if context in context_map:
        return context_map[context](prefix)

    return glob.glob(prefix + "*")


@blueprint.route('/autocomplete')
def autocomplete():
    pref = request.args.get('prefix', '')

    context = request.args.get("context")
    if context:
        return make_response(jsonify(getContext(context, pref)), 200)

    return make_response(jsonify(glob.glob(pref + "*")), 200)


def highlight_code(code, type):
    try:
        lex = get_lexer_by_name(type)
        form = HtmlFormatter(linenos=True, style="colorful", noclasses=True)
        return highlight(code, lex, form)
    except Exception as e:
        print(e)
        return code

def setup_app(app):
    for kk, vv in ALL_BLUEPRINTS.items():
        if hasattr(vv, "setup_app"):
            vv.setup_app(app)


def template_globals(d):
    # Strings are not mutable -- This class just delays so we get the current value
    class DelayCopyRightLink:
        def __str__(self):
            return COPYRIGHT_LINK

    class DelayCopyRightMessage:
        def __str__(self):
            return COPYRIGHT_MESSAGE

    def logo_large():
        return os.path.join(IMAGES_PATH, LOGO_LARGE)

    def logo_small():
        return os.path.join(IMAGES_PATH, LOGO_SMALL)

    def logo_icon():
        return os.path.join(IMAGES_PATH, LOGO_ICON)

    def home_file():
        return HOME_FILE

    def title_name():
        return TITLE_NAME

    def paraview_configured(): return current_app.config["PARAVIEW"] > 0

    def theia_configured(): return current_app.config["THEIA"] > 0 
    
    def get_uuid(): return uuid.uuid4().hex

    d["COPYRIGHT_LINK"] = DelayCopyRightLink()
    d["COPYRIGHT_MESSAGE"] = DelayCopyRightMessage()
    d["ALL_BLUEPRINTS"] = ALL_BLUEPRINTS
    d["logo_large"] = logo_large
    d["logo_small"] = logo_small
    d["logo_icon"] = logo_icon
    d["home_template"] = home_file
    d["title_name"] = title_name
    d["highlight_code"] = highlight_code
    d["HASVNV"] = blueprints.HAS_VNV
    d["paraview_configured"] = paraview_configured
    d["theia_configured"] = theia_configured
    d["getUUID"] = get_uuid

    
    for kk, vv in ALL_BLUEPRINTS.items():
        if hasattr(vv, "template_globals"):
            vv.template_globals(d)

