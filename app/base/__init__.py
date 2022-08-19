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
from pygments.lexers import guess_lexer, guess_lexer_for_filename, get_lexer_by_name

from . import blueprints
from .utils.mongo import list_mongo_collections, Configured, BrandNew

from werkzeug.security import generate_password_hash, check_password_hash
from app.Directory import VNV_DIR_PATH
from .utils.utils import render_error

from .. import Directory
from ..models.VnVInputFile import VnVInputFile, add_input_file_type

blueprint = Blueprint(
    'base',
    __name__,
    url_prefix='',
    template_folder='templates'
)


def config(conf):
    global PASSWORD
    PASSWORD = generate_password_hash(conf.passw)
    global AUTHENTICATE
    AUTHENTICATE = conf.auth


def updateBranding(config, pd):
    logo = config.get("logo", {})
    if "small" in logo and os.path.exists(os.path.join(pd, logo["small"])):
        global LOGO_SMALL
        LOGO_SMALL = os.path.basename(logo["small"])
        shutil.copy(os.path.join(pd, logo["small"]), IMAGES_DIR)

    if "icon" in logo and os.path.exists(os.path.join(pd, logo["icon"])):
        global LOGO_ICON
        LOGO_ICON = os.path.basename(logo["icon"])
        shutil.copy(os.path.join(pd, logo["icon"]), IMAGES_DIR)

    if "large" in logo and os.path.exists(os.path.join(pd, logo["large"])):
        global LOGO_LARGE
        LOGO_LARGE = os.path.basename(logo["large"])
        shutil.copy(os.path.join(pd, logo["large"]), IMAGES_DIR)

    if "home" in config:
        global HOME_FILE
        HOME_FILE = "includes/home_custom.html"
        shutil.copy(os.path.join(pd, config["home"]), os.path.join(TEMPLATES_DIR, HOME_FILE))

    if "title" in config:
        global TITLE_NAME
        TITLE_NAME = config["title"]

    copy = config.get("copyright", {})
    if "message" in copy:
        global COPYRIGHT_MESSAGE
        COPYRIGHT_MESSAGE = copy["message"]
        print("Update Copyright Message", COPYRIGHT_MESSAGE)

    if "link" in copy:
        global COPYRIGHT_LINK
        COPYRIGHT_LINK = copy["link"]
        print("Update Copyright Link", COPYRIGHT_LINK)

    if "blueprints" in config:
        bp = config["blueprints"]
        for k, v in bp.items():
            temp_bp_dir = os.path.join(VNV_DIR_PATH, "temp", "blueprints", k)
            if os.path.exists(temp_bp_dir):
                shutil.rmtree(temp_bp_dir)

            print("Adding Additional module ", k)
            shutil.copytree(os.path.join(pd, v), temp_bp_dir, dirs_exist_ok=True)
            threading.Event().wait(1)
            ALL_BLUEPRINTS[k] = importlib.import_module("app.temp.blueprints." + k)

    if config.get("exclude_parents", False):
        blueprints.inputfiles.vnv_executables = {}

    for key, value in config.get("executables", {}).items():
        blueprints.inputfiles.vnv_executables[key] = [
            os.path.join(pd, value["filename"]),
            value.get("description", "No Description Available"),
            value.get("defaults", {}),
            value.get("packageName", "VnV")
        ]

    for key, value in config.get("plugins", {}).items():
        blueprints.inputfiles.vnv_plugins[key] = os.path.join(pd, value.get("filename", ""))

    blueprints.files.load_defaults(config.get("reports", {}))


FIRST_TIME = None
if FIRST_TIME is None:
    FIRST_TIME = False

    AUTHENTICATE = False
    PASSWORD = generate_password_hash("password")
    COOKIE_PASS = uuid.uuid4().hex
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

    ALL_BLUEPRINTS = blueprints.all_blueprints

    a = os.getenv("VNV_CONFIG")
    if a is not None:

        for file in a.split(":"):
            try:

                print("Loading configuration from: ", file)
                with open(file, 'r') as w:
                    updateBranding(json.load(w), os.path.dirname(file))

            except Exception as e:
                print(e)
                pass

    blueprints.inputfiles.vnv_executables["Custom"] = ["", "Custom Application", {}, "N/A"]

    for k, v in ALL_BLUEPRINTS.items():
        blueprint.register_blueprint(v.blueprint)


def GET_COOKIE_TOKEN():
    return COOKIE_PASS



def verify_cookie(cook):
    if cook is not None and cook == COOKIE_PASS:
        return True
    return False


@blueprint.before_request
def check_valid_login():
    if not AUTHENTICATE:
        return

    login_valid = verify_cookie(request.cookies.get("vnv-login"))
    if request.form.get("__token__") is not None:
        if not check_password_hash(PASSWORD, request.form["__token__"]):
            return make_response("Authorization Failed", 401)

    elif request.endpoint and request.endpoint != "base.login" and 'static' not in request.endpoint and not login_valid:
        return render_template('login.html', next=request.url)


@blueprint.route('/')
def default_route():
    return render_template('index.html', segment='index')


@blueprint.route('/theia')
def theia_route():
    # This route should get intercepted by the "serve" app, so, when
    # serving, this should never be called. This button is just a placeholder
    # for the serve app -- should really allow the serve app to add buttons.
    return render_error(200, "Eclipse Theia is not configured", nohome=True)


@blueprint.route('/paraview')
def paraview_route():
    # This route should get intercepted by the "serve" app, so, when
    # serving, this should never be called. This button is just a placeholder
    # for the serve app -- should really allow the serve app to add buttons.
    return render_error(200, "Visualzier is not configured", nohome=True)

@blueprint.route('/glvis')
def glvis_route():
    # This route should get intercepted by the "serve" app, so, when
    # serving, this should never be called. This button is just a placeholder
    # for the serve app -- should really allow the serve app to add buttons.
    return render_error(200, "Glvis is not configured", nohome=True)


@blueprint.route("/ide")
def ide_route():
    return render_template("ide.html")


@blueprint.route("/viz")
def viz_route():
    return render_template("para.html")


@blueprint.route("/browse")
def browse_route():
    return render_template("browse.html")


@blueprint.route("/term")
def term_route():
    return render_template("terminal_.html")


@blueprint.route('/avatar/<username>')
def avatar_route(username):
    return send_file("static/assets/images/user/AVATARS.png")


@blueprint.route('/login', methods=["POST"])
def login():
    if not AUTHENTICATE:
        return make_response(redirect("/"))

    if check_password_hash(PASSWORD, request.form.get("password")):
        response = make_response(redirect("/"))
        response.set_cookie('vnv-login', GET_COOKIE_TOKEN())
        return response
    return render_template("login.html", error=True)


@blueprint.route('/logout', methods=["POST"])
def logout():
    global COOKIE_PASS
    COOKIE_PASS = uuid.uuid4().hex
    response = make_response(redirect("/"))
    response.set_cookie('vnv-login', "", expires=0)
    response.set_cookie('vnv-container-ip', "", expires=0)
    response.set_cookie(current_app.config["LOGOUT_COOKIE"], "", expires=0)
    return response


@blueprint.route("icon")
def icon():
    p = request.args.get("package")
    return send_file("static/assets/images/close.png")


@blueprint.route("/")
def home():
    return render_template("index.html", segment="index")


def available_ports():
    return range(14000, 14010)


context_map = {
    "json_file": lambda x: glob.glob(x + "*"),
    "adios_file": lambda x: glob.glob(x + "*"),
    "json_http": lambda x: [str(a) for a in available_ports()],
    "json_socket": lambda x: [str(a) for a in available_ports()],
    "saved": lambda x: list_mongo_collections()
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

    def theia_url():
        return current_app.config["THEIA_URL"]

    def paraview_url():
        return current_app.config["PARAVIEW_URL"]

    d["COPYRIGHT_LINK"] = DelayCopyRightLink()
    d["COPYRIGHT_MESSAGE"] = DelayCopyRightMessage()
    d["ALL_BLUEPRINTS"] = ALL_BLUEPRINTS
    d["logo_large"] = logo_large
    d["logo_small"] = logo_small
    d["logo_icon"] = logo_icon
    d["theia_url"] = theia_url

    d["home_template"] = home_file
    d["paraview_url"] = paraview_url
    d["title_name"] = title_name
    d["highlight_code"] = highlight_code

    for kk, vv in ALL_BLUEPRINTS.items():
        if hasattr(vv, "template_globals"):
            vv.template_globals(d)
