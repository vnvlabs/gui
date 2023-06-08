import json
import re

import jsonschema
from flask import Blueprint, request, render_template, jsonify, make_response, render_template_string
from werkzeug.utils import redirect

from app.base.utils.utils import render_error

from app.models.VnVConnection import MAIN_CONNECTION, SetMainConnection, SetFileConnection, VnVLocalConnection
from app.models.readers import LocalFile, get_hive_file

try:
    from app.models.VnVFile import VnVFile
    HAS_VNV = True
except:
    HAS_VNV = False

blueprint = Blueprint(
    'browser',
    __name__,
    url_prefix='/browser',
    template_folder='templates'
)
@blueprint.route("")
def browse_route():
    return render_template("browser/browse.html", model="inline-")

@blueprint.route("/edit/<int:id_>", methods=["GET", "POST"])
def edit_file(id_):
    filename=request.args.get("filename")

    if id_ == 1000 or not HAS_VNV:
        connection = MAIN_CONNECTION()

    if HAS_VNV:
        if connection is None and id_ in VnVFile.FILES:
            connection = VnVFile.FILES[id_].connection

        if connection is None:
            from app.models.VnVInputFile import VnVInputFile
            if id_ in VnVInputFile.FILES:
                connection = VnVInputFile.FILES[id_].connection

    if isinstance(connection,VnVLocalConnection):
        return make_response(redirect(f"/ide?filename={filename}"), 302)
    else:
        return render_error(502, "Editing is not supported on remote connections yet", nohome=False)

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
        render_args = {a[7:]: request.args[a] for a in request.args if a.startswith("render_")}
        file = LocalFile(filename, id_, connection, reader=reader, **render_args)
        return make_response(file.render(modal=modal),200)


    except Exception as e:
        return render_error(203,"Could not open file", nohome=True)

@blueprint.route("/hive/autocomplete", methods=["GET"])
def hive_autocomplete_endpoint():
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
def hive_save_endpoint():
    text = request.args.get("val")
    schemaId = request.args.get("schema")

    hive = get_hive_file(schemaId)
    if hive is not None:
        return make_response(jsonify(hive.save(text)),200)

    return make_response(jsonify({"error" : "file not found"}), 404)

@blueprint.route("/hive/format", methods=["POST"])
def hive_format_endpoint():
    text = request.args.get("val")
    schemaId = request.args.get("schema")

    hive = get_hive_file(schemaId)
    if hive is not None:
        return make_response(hive.format(text),200)

    return make_response(text, 404)

@blueprint.route("/hive/validate", methods=["GET"])
def hive_validate_endpoint():
    text = request.args.get("val")
    schemaId = request.args.get("schema")

    hive = get_hive_file(schemaId)
    if hive is not None:
        return make_response(jsonify(hive.validate(text)),200)
    return make_response(jsonify([]), 404)

@blueprint.route("/hive/schema", methods=["POST"])
def hive_schema_endpoint():

    schemaId = request.args.get("schema")
    exe = request.args.get("val")

    hive = get_hive_file(schemaId)
    if hive is not None:
        result = hive.set_schema(exe, reload=True)
        return make_response(result,200)
    return make_response("Error: File not found ", 404)

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

        if reader == "connection":
            return render_template("browser/connection.html", vnvfileid=id_, modal=modal, filename=filename,
                                   connection=connection)

        if not connection.connected():
            return render_template("browser/connection.html", vnvfileid=id_, modal=modal, filename=filename,
                                   connection=connection, reason="disconnected")

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

        if not connection.exists(filename):
            return render_template("browser/connection.html", vnvfileid=id_, modal=modal, filename=filename,
                                   connection=connection, reason="does not exist")

        try:

            file = LocalFile(filename, id_, connection, reader=reader, **render_args)
            return render_template("browser/browser.html", file=file, modal=modal)

        except Exception as e:
            return render_template("browser/browser.html",
                                   file=LocalFile(connection.home(), id_, connection, **render_args), error=str(e),
                                   modal=modal)

    except Exception as e:
        return render_error(501, "Error Loading File:" + str(e))


@blueprint.route('/close_connection/<int:id_>')
def close_connection(id_):
    if id_ == 1000 or not HAS_VNV:
        MAIN_CONNECTION().disconnect()
    else:
        with VnVFile.find(id_) as file:
            file.connection.disconnect()
    return make_response("Ok", 200)


@blueprint.route('/open_connection/<int:id_>', methods=["POST"])
def open_connection(id_):
    local = request.form.get('local', False)
    uname = request.form.get("username")
    domain = request.form.get('domain')
    port = int(request.form.get('port'))
    password = request.form.get("password")

    if id_ == 1000 or not HAS_VNV:
        r = SetMainConnection(local, uname, domain, password, port)
    else :
        with VnVFile.find(id_) as file:
            r = SetFileConnection(file, local, uname, domain, password, port)

    return make_response("Ok", 200 if r else 201)
