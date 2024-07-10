import uuid
import sys
from flask import Blueprint
from flask import render_template, url_for, request
import os

moose_dir = os.getenv('MOOSE_DIR', os.path.join(os.path.dirname(__file__), '..', '..','..','..','..','..','applications','moose'))
sys.path.append(os.path.join(moose_dir,"python"))

from .moose import *

#This is the minimal example of a vnv compatible blueprint that can be added into the main
#gui through the input file. The blueprint must match this template to ensure that it all
#works together with all the other blueprints.

#Step 0:

##### Step 1 -- CHANGE THIS NAME TO BE UNIQUE TO THIS BLUEPRINT
TEMPLATE_NAME="hive"

# Blueprint must be named "blueprint"
blueprint = Blueprint(
    TEMPLATE_NAME,
    __name__,
    template_folder='templates',
    static_folder="static",
    url_prefix="/" + TEMPLATE_NAME
)



@blueprint.route("/hive/autocomplete", methods=["GET"])
def autocomplete():
    text = request.args.get("val")
    row = request.args.get("row")
    col = request.args.get("col")
    pre = request.args.get("pre")
    schema = request.args.get("schema")
    hive = get_hive_file(schema)
    if hive is not None:
        autocomplete = hive.autocomplete(text=text, row=row, col=col, prefix=pre)
        return make_response(jsonify(autocomplete),200)
    return make_response(jsonify([]), 404)


@blueprint.route("/hive/save", methods=["POST"])
def save():
    text = request.args.get("val")
    schemaId = request.args.get("schema")

    hive = get_hive_file(schemaId)
    if hive is not None:
        return make_response(jsonify(hive.save(text)),200)

    return make_response(jsonify({"error" : "file not found"}), 404)

@blueprint.route("/hive/format", methods=["GET"])
def format():
    text = request.args.get("val")
    schemaId = request.args.get("schema")

    hive = get_hive_file(schemaId)
    if hive is not None:
        return make_response(hive.format(text),200)

    return make_response(text, 404)

@blueprint.route("/hive/validate", methods=["GET"])
def validate():
    text = request.args.get("val")
    schemaId = request.args.get("schema")

    hive = get_hive_file(schemaId)
    if hive is not None:
        return make_response(jsonify(hive.validate(text)),200)
    return make_response(jsonify([]), 404)

@blueprint.route("/hive/schema", methods=["POST"])
def schema():

    schemaId = request.args.get("schema")
    exe = request.args.get("val")

    hive = get_hive_file(schemaId)
    if hive is not None:
        result = hive.set_schema(exe, reload=True)
        return make_response(result,200)
    return make_response("Error: File not found ", 404)

@blueprint.route("/hive/mesh", methods=["POST"])
def mesh():
    text = request.args.get("val")
    schemaId = request.args.get("schema")

    hive = get_hive_file(schemaId)
    if hive is not None:
        mess,code = hive.regenerate_mesh(text)
        return make_response(mess,code)
    return make_response(jsonify([]), 404)
#Get the full route


def get_route(function, **kwargs):
    return url_for("base." + TEMPLATE_NAME + "." + function, **kwargs)

# Get the full url path
def get_url(path):
    return "/" + TEMPLATE_NAME + path

# Get the url path for a static file.
def get_static_raw(path):
    return url_for("base." + TEMPLATE_NAME + ".static", filename=path)

def get_template_file(filename):
    return get_file(TEMPLATE_NAME + "/" + filename)

# Render a file inside the VnV GUI
def get_file(path):
    return get_route("segment", content=path)



# VnV Will call this function. Whatever is entered here can be used
# globally in templates within the {{...}} commands.
def template_globals(global_template_dict):
    global_template_dict[TEMPLATE_NAME] = {
        "route" : get_route,
        "url" : get_url,
        "static" : get_static_raw,
        "file": get_file
    }

## Default route to render template file within the VnV Gui
@blueprint.route("fetch")
def segment():
   try:
    content = request.args.get("content")
    return render_template(content)
   except:
       return render_template("includes/page-not-found.html")


from app.models.readers import FILE_READERS, EXT_MAP

FILE_READERS["hive"] = render_hive
EXT_MAP[".i"] = "hive"

