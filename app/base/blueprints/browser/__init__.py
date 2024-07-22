import json
import os.path
import re

import jsonschema
from flask import Blueprint, request, render_template, jsonify, make_response, render_template_string
from werkzeug.utils import redirect

from app.base.utils.utils import render_error

from app.models.VnVConnection import MAIN_CONNECTION, VnVLocalConnection
from app.models.readers import LocalFile

try:
    from app.models.VnVFile import VnVFile

    HAS_VNV = True
except:
    HAS_VNV = False

from app.models.VnVInputFile import VnVInputFile

blueprint = Blueprint(
    'browser',
    __name__,
    url_prefix='/browser',
    template_folder='templates',
    static_folder='static'
)
@blueprint.route("")
def browse_route():
    filename = request.args.get("filename","")
    if "nohead" in request.args:
        return render_template("browser/browsen.html", model="inline-", filename=filename)
    return render_template("browser/browse.html", model="inline-", filename=filename)



@blueprint.route("/render/<int:id_>", methods=["GET", "POST"])
def render(id_):
    reader = request.args.get("reader")
    filename = request.args.get("filename", "")
    modal = request.args.get("modal", "")

    connection = None
    if id_ == 1000 or not HAS_VNV:
        connection = MAIN_CONNECTION()

    if HAS_VNV:
        if connection is None and id_ in VnVFile.FILES:
            connection = VnVFile.FILES[id_].connection

        if connection is None:
            from app.models.VnVInputFile import VnVInputFile
            if id_ in VnVInputFile.FILES:
                connection = VnVInputFile.FILES[id_].connection

    try:
        filename = os.path.expandvars(filename)
        render_args = {a[7:]: request.args[a] for a in request.args if a.startswith("render_")}
        file = LocalFile(filename, id_, connection, reader=reader, **render_args)
        return make_response(file.render(modal=modal),200)

    except Exception as e:
        return render_error(203,"Could not open file", nohome=True)

@blueprint.route('/save_file/<int:id_>', methods=["GET","POST"])
def save_file(id_):

    if id_ == 1000 or not HAS_VNV:
        connection = MAIN_CONNECTION()
    elif id_ in VnVFile.FILES:
         connection = VnVFile.FILES[id_].connection
    elif id_ in VnVInputFile.FILES:
         connection = VnVInputFile.FILES[id_].connection
    else:
        connection = MAIN_CONNECTION()

    connection.write(request.form["value"], request.form["filename"])
    return make_response("Ok", 200)

@blueprint.route("/reader/<int:id_>", methods=["GET", "POST"])
def reader(id_):
    try:
        reader = request.args.get("reader")
        filename = request.args.get("filename", "")
        modal = request.args.get("modal", "")
        connection = None
        if id_ == 1000 or not HAS_VNV:
            connection = MAIN_CONNECTION()

        if HAS_VNV:
            if connection is None and id_ in VnVFile.FILES:
                connection = VnVFile.FILES[id_].connection

            if connection is None:
                from app.models.VnVInputFile import VnVInputFile
                if id_ in VnVInputFile.FILES:
                    connection = VnVInputFile.FILES[id_].connection



        render_args = {a[7:]: request.args[a] for a in request.args if a.startswith("render_")}

        if reader == "upload":
            return render_template("browser/upload.html", vnvfileid=id_, filename=filename, reason="", modal=modal,
                                   connection=connection)

        if reader == "actual_upload":
            try:
                filename = request.form["filename"]
                request.files["file"].save(filename)
            except Exception as e:
                return render_template("browser/upload.html", vnvfileid=id_, filename=filename, modal=modal,
                                       reason=str(e), connection=connection)

        if len(filename) == 0:
            filename = connection.home()

        try:
            filename = os.path.expandvars(filename)
            if connection.exists(filename):
                file = LocalFile(filename, id_, connection, reader=reader, **render_args)
                return render_template("browser/browser.html", file=file, modal=modal)
            return render_error(501, "File Does not exist: " + filename)

        except Exception as e:
            return render_template("browser/browser.html",
                                   file=LocalFile(connection.home(), id_, connection, **render_args), error=str(e),
                                   modal=modal)

    except Exception as e:
        return render_error(501, "Error Loading File:" + str(e))



