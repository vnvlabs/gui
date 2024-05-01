import json
import re

import jsonschema
from flask import Blueprint, request, render_template, jsonify, make_response, render_template_string
from werkzeug.utils import redirect

from app.base.utils.utils import render_error

from app.models.VnVConnection import MAIN_CONNECTION, SetMainConnection, SetFileConnection, VnVLocalConnection
from app.models.readers import LocalFile

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
    filename = request.args.get("filename","")
    return render_template("browser/browse.html", model="inline-", filename=filename)
    
@blueprint.route("/edit/<int:id_>", methods=["GET", "POST"])
def edit_file(id_):
    filename=request.args.get("filename")
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

            if connection.exists(filename):
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
