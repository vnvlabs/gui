# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import glob
import json
import os
import textwrap
import uuid
from pathlib import Path

from flask import Blueprint, make_response, jsonify
from flask import render_template, redirect, url_for, request

from app.Directory import STATIC_FILES_DIR
from app.models import VnVFile
from app.models.VnVInputFile import VnVInputFile
from ..files import get_file_from_runinfo
from ...utils.utils import render_error
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from werkzeug.utils import redirect
from pygments.lexers import guess_lexer, guess_lexer_for_filename, get_lexer_by_name

vnv_executables = {}
vnv_plugins = {}

blueprint = Blueprint(
    'inputfiles',
    __name__,
    template_folder='templates',
    url_prefix="/inputfiles"
)

@blueprint.route('/new', methods=["POST"])
def new():
    try:

        c = request.form.get("executable")
        if c == "Custom":
            path = request.form["path"]
        else:
            path = os.path.join(VnVInputFile.VNV_PREFIX, vnv_executables.get(c)["filename"])

        file = VnVInputFile.add(request.form["name"], path)

        return make_response(redirect(url_for("base.inputfiles.view", id_=file.id_)),302)

    except Exception as e:
        return render_error(501, "Error Loading File")


@blueprint.route('/delete/<int:id_>', methods=["POST"])
def delete(id_):
    VnVInputFile.removeById(id_)
    return "success", 200


@blueprint.route('/disconnect/<int:id_>', methods=["POST"])
def disconnect(id_):
    with VnVInputFile.find(id_) as file:
        file.connection.disconnect();
        return render_template("inputfiles/connection_content.html", file=file)


@blueprint.route('/save_input/<int:id_>', methods=["POST"])
def save_input_file(id_):
    with VnVInputFile.find(id_) as file:
        form = request.get_json()
        file.saveInput(form["value"])
        return make_response("", 200)


@blueprint.route('/save_exec/<int:id_>', methods=["POST"])
def save_exec(id_):
    with VnVInputFile.find(id_) as file:
        form = request.get_json()
        file.exec = form["value"]
        return make_response("", 200)




@blueprint.route('/validate/<string:comp>/<int:id_>', methods=["POST"])
def validate_input(comp, id_):
    with VnVInputFile.find(id_) as file:
        form = request.get_json()
        if comp == "inputfile":
            r = file.validateInput(form["value"]);
        else:
            r = []

        return make_response(jsonify(r), 200 if len(r) == 0 else 201)


@blueprint.route('/load_input/<int:id_>', methods=["POST"])
def load_input(id_):
    path = request.form["filename"]
    with VnVInputFile.find(id_) as file:
        file.loadfile = path

        if not file.connection.connected():
            return make_response("Please open a connection before continuing", 201)

        if file.connection.exists(path):
            if file.connection.is_dir(path):
                return make_response("Cannot load a directory", 201)
            try:
                p = file.connection.download(path)
                txt = Path(p).read_text()
                return make_response(txt, 200)
            except Exception as e:
                return make_response(f"Something went wrong ({e}", 202)
        else:
            return make_response("File does not exist", 200)


@blueprint.route('/load_exec/<int:id_>', methods=["POST"])
def load_exec(id_):
    path = request.form["filename"]
    with VnVInputFile.find(id_) as file:
        file.execFile = path

        if not file.connection.connected():
            return make_response("Please open a connection before continuing", 201)

    if file.connection.exists(path):
        if file.connection.is_dir(path):
            return make_response("Cannot load a directory", 201)
        try:
            p = file.connection.download(path)
            txt = Path(p).read_text()
            return make_response(txt, 200)
        except Exception as e:
            return make_response(f"Something went wrong ({e}", 202)
    else:
        return make_response("File does not exist", 200)




@blueprint.route('/connected/<int:id_>', methods=["GET"])
def connected(id_):
    with VnVInputFile.find(id_) as file:
        return make_response("", 200 if file.connection.connected() else 201)


@blueprint.route('/autocomplete/<string:comp>/<int:id_>', methods=["GET"])
def input_autocomplete(comp, id_):
    row = request.args["row"]
    col = request.args["col"]
    pre = request.args["pre"]
    val = request.args["val"].split("\n")
    with VnVInputFile.find(id_) as file:
        if hasattr(file, "autocomplete_" + comp):
            r = getattr(file, "autocomplete_" + comp)(row, col, pre, val)
            return make_response(jsonify(r), 200)

    return make_response(jsonify([]), 200)


@blueprint.route('/update_main_header/<int:id_>')
def main_header(id_):
    with VnVInputFile.find(id_) as file:
        data = {
            "header": render_template("inputfiles/main_header_content.html", file=file),
            "spec": file.spec,
            "desc": file.get_executable_description()
        }
        return make_response(jsonify(data), 200)
    return make_response("Error", 500)


@blueprint.route('/get_spec/<int:id_>')
def get_spec(id_):
    with VnVInputFile.find(id_) as file:
        return make_response(file.spec, 200)


@blueprint.route('/autocomplete')
def autocomplete():
    pref = request.args.get('prefix', '')
    file = request.args.get("file")
    try:
        with VnVInputFile.find(int(file)) as f:
            return make_response(jsonify(f.connection.autocomplete(pref)), 200)
    except:
        make_response(jsonify(glob.glob(pref + "*")), 200)


@blueprint.route('/get_desc/<int:id_>')
def get_desc(id_):
    with VnVInputFile.find(id_) as file:
        return make_response(file.get_executable_description(), 200)


@blueprint.route('/configure/<int:id_>', methods=["POST"])
def configure(id_):
    with VnVInputFile.find(id_) as file:

        if "local" in request.form:
            file.setConnectionLocal()
        else:
            username = request.form["username"]
            port = request.form["port"]
            domain = request.form["domain"]
            password = request.form["password"]
            file.setConnection(domain, username, password, port)

        res = file.setFilename(request.form.get("application"), request.form.get("specDump"), request.form.get("plugs"))
        if res:
            return redirect(url_for(".view", id_=id_, error="Application Configuration Completed Successfully."), 302)
        return redirect(url_for(".view", id_=id_, error="Configuration Failed!"), 302)


@blueprint.route('/view/<int:id_>')
def view(id_):

    try:
        with VnVInputFile.find(id_) as file:
            return render_template("inputfiles/view.html", file=file, error=request.args.get("error"))
    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_error(501, "Error Loading File")


@blueprint.route('/joblist/<int:id_>')
def joblist(id_):
    try:
        with VnVInputFile.find(id_) as file:
            return render_template("inputfiles/joblist.html", file=file)
    except Exception as e:
        return render_error(501, "Error Loading File")



@blueprint.route('/delete_job/<int:id_>/<jobid>', methods=["POST"])
def delete_job(id_, jobid):
    with VnVInputFile.find(id_) as file:
        file.connection.delete_job(jobid);
        return render_template("inputfiles/joblist.html", file=file)
    return render_error(401, "Huh")


@blueprint.route('/refresh_job/<int:id_>/<jobid>', methods=["GET"])
def refresh_job(id_, jobid):
    with VnVInputFile.find(id_) as file:
        file.refresh_job(jobid);
        return make_response(jsonify(file.refresh_job(jobid)), 200)
    return render_error(jsonify({"stdout": "no file found", "errorcode": 100}), 200)


@blueprint.route('/cancel_job/<int:id_>/<jobid>', methods=["POST"])
def cancel_job(id_, jobid):
    with VnVInputFile.find(id_) as file:
        file.connection.cancel_job(jobid);
        res = render_template("inputfiles/joblist.html", file=file)
        return res
    return render_error(401, "Huh")


@blueprint.route('/openreport/<int:id_>')
def openreport(id_):
    try:
        with VnVInputFile.find(id_) as file:
            pref = os.path.join(request.args["dir"], "vnv_" + request.args["id"] + "_")
            reports = file.connection.autocomplete(pref)

            if "confirmed" in request.args:
                for i in reports:
                    with open(file.connection.download(i), 'r') as ff:
                        ff = get_file_from_runinfo(json.load(ff))
                        return make_response(url_for('base.files.view', id_=ff.id_), 200)

            return make_response("Error", 201)

    except Exception as e:
        print(e)
        return make_response("Error", 201)


@blueprint.route('/delete-all', methods=["POST"])
def delete_all():
    VnVInputFile.delete_all()
    return make_response("Complete", 200)


@blueprint.route('/update_display_name/<int:id_>', methods=["POST"])
def update_display_name(id_):
    with VnVInputFile.find(id_) as file:
        file.displayName = request.args.get("new", file.displayName)
        return make_response(file.displayName, 200)



def highlight_code(code, type):
    try:
        lex = get_lexer_by_name(type)
        form = HtmlFormatter(linenos=True, style="colorful", noclasses=True)
        return highlight(code, lex, form)
    except Exception as e:
        print(e)
        return code


@blueprint.route('/execute/<int:id_>')
def execute(id_):
    try:
        with VnVInputFile.find(id_) as file:
            if "dryrun" in request.args:
                script, name = file.script(request.args.get("val", ""), "SAMPLE")
                return make_response(script, 200)
            else:
                return make_response(file.execute(request.args.get("val", "")), 200)

    except Exception as e:
        print(e)
        return render_error(501, "Error Loading File")


def list_vnv_executables():
    return [[k, v["description"], v["package"]] for k, v in vnv_executables.items()]


def template_globals(globs):
    globs["inputfiles"] = VnVInputFile.FILES
    globs["list_vnv_executables"] = list_vnv_executables
