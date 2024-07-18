# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import json
import os
import threading

from flask import Blueprint, make_response, jsonify, flash
from flask import render_template, redirect, url_for, request
import socket

from app import Directory
from . import viewers
from app.models.VnVFile import VnVFile
from ...registration import list_registered_reports
from ...utils.utils import render_error

blueprint = Blueprint(
    'files',
    __name__,
    template_folder='templates',
    url_prefix="/files"
)
blueprint.register_blueprint(viewers.blueprint, url_prefix="/viewers")


def get_file_template_root():
    return Directory.RENDERS_DIR


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('0.0.0.0', port)) == 0


class FastReadCounter(object):
    def __init__(self):
        self.value = 0
        self._lock = threading.Lock()

    def increment(self):
        with self._lock:
            self.value += 1
            return self.value - 1


PORTCOUNT = FastReadCounter()


def get_open_port():
    return 14000 + PORTCOUNT.increment()


@blueprint.route('/autostart', methods=["POST"])
def autostart():
    try:
        port = get_open_port()
        if port is None:
            return make_response("error - no available ports", 401)

        file = VnVFile.add(
            request.form["name"],
            str(port),
            request.form["reader"],
            get_file_template_root(),
            username=request.form.get("username"),
            password=request.form.get("password"),
            workflowJob=request.form.get("workflowJob", ""),
            workflowName=request.form.get("workflowName", "")
        )

        return make_response(f'0.0.0.0:{port}', 200)
    except Exception as e:
        return make_response("error", 501)


@blueprint.route('/new', methods=["POST"])
def new():
    try:

        # If there was a job name, then look for a file with that jobname
        # if it exists, return that
        if "jobName" in request.form:
            file = VnVFile.findByJobName(request.form["jobName"])
            if file is not None:
                return redirect(url_for("base.files.view", id_=file.id_))

        # No jobname so we should load a new file.
        fname = request.form["filename"]

        reader = "file"
        if reader == "file":
            if not os.path.exists(fname):
                return render_error(501, "Error Loading File - Path does not exist")
            elif not os.path.isdir(fname):
                return render_error(501, "Error Loading File - Path is not a directory")

        file = VnVFile.add(
                request.form["name"],
                fname,
                reader,
                get_file_template_root(),
                username=request.form.get("username"),
                password=request.form.get("password")
        )

        return redirect(url_for("base.files.view", id_=file.id_))
    except Exception as e:
        return render_error(501, "Error Loading File" + str(e))


@blueprint.route('/update_display_name/<int:id_>', methods=["POST"])
def update_display_name(id_):
    with VnVFile.find(id_) as file:
        file.update_dispName(request.args.get("new", file.dispName))
        return make_response(file.dispName, 200)


@blueprint.route('/delete-all', methods=["POST"])
def delete_all():
    VnVFile.delete_all()
    return make_response("Complete", 200)


def get_file_from_runinfo(runinfo):
    # if the job name matches then its that one
    f = VnVFile.findByJobName(runinfo["name"])
    if f is not None:
        return f

    engineInfo = runinfo["engine"]
    # if the engine name matches and the read er matches then its prob that one.
    for k, v in VnVFile.FILES.items():
        if v.filename == engineInfo["filename"]:
            return v

    # make a new one.
    fname = engineInfo.pop("filename")
    reader = engineInfo.pop("reader")
    ff = VnVFile.add(runinfo["name"], fname, reader, get_file_template_root(), False, **engineInfo)
    return ff


@blueprint.route('/delete/<int:id_>', methods=["POST"])
def delete(id_):
    refresh = bool(request.args.get("refresh"))
    VnVFile.removeById(id_, refresh)
    if (refresh):
        return make_response(url_for('base.files.view', id_=id_))
    return "success", 200


@blueprint.route("/source/<int:id_>/<int:dataId>")
def source(id_, dataId):
    with VnVFile.find(id_) as file:
        d = file.getById(dataId);
        return render_template("files/sourcemap.html", sourcemap=file.getSourceMap(dataId))

@blueprint.route('/comm/<int:id_>')
def comm(id_):
    with VnVFile.find(id_) as file:
        commId = request.args.get("cid")
        commrender = file.getCommRender(commId)
        return render_template("files/comm.html", commrender=commrender)

@blueprint.route('/comm_data/<int:id_>/<int:ipid>')
def comm_data(id_, ipid):
    with VnVFile.find(id_) as file:
        commId = request.args.get("cid")
        commrender = file.get_injection_point_comm_data(ipid)
        return make_response(jsonify(commrender),200)


@blueprint.route("/workflow/node_image/<string:nodeType>")
def workflow_node_image(nodeType):
    return redirect("/static/assets/images/pink-circle.jpeg")


@blueprint.route("/workflow/render_job/<int:id_>")
def workflow_render_job(id_):
    try:
        with VnVFile.find(id_) as file:
            creator = request.args.get("creator")
            name = request.args.get("name")
            code = request.args.get("code")
            if creator is not None:
                c = creator.split(":")
                return make_response(file.render_workflow_job(c[0], c[1], code), 200)

    except Exception as e:
        print(e)
    return make_response("", 200)

@blueprint.route("/workflow/raw_rst/<int:id_>")
def workflow_render_rst(id_):
    try:
        with VnVFile.find(id_) as file:
            creator = request.args.get("creator")
            if creator is not None:
                c = creator.split(":")
                return make_response(file.render_workflow_rst(c[0], c[1], request.args.get("jobName")), 200)

    except Exception as e:
        print(e)
    return make_response("", 200)


@blueprint.route('/data', methods=["GET"])
def data():
    fileId = request.args.get('fileId', type=int)
    nodeId = request.args.get('nodeId')
    with VnVFile.find(fileId) as file:
        return make_response(jsonify(file.getDataChildren(nodeId)), 200)



@blueprint.route('/data_root/<int:id_>', methods=["GET"])
def data_root(id_):
    # One layer of children -- all others just issue children = ""
    node = request.args.get("id", "#")

    if node == "#":
        with VnVFile.find(id_) as file:
            return make_response(jsonify(file.getDataRoot()), 200)
    else:
        return make_response(jsonify([]), 200)


@blueprint.route('/view')
def view():
    try:
        return render_template("files/tab-view.html")
    except Exception as e:
        print(e)
        return render_error(501, str(e))

@blueprint.route('/prov/<int:id_>')
def prov(id_):
    try:
        with VnVFile.find(id_) as file:
            return render_template("files/provenance.html", file=file)
    except Exception as e:
        print(e)
        return render_error(501, str(e))

@blueprint.route('/browser/<int:id_>')
def browser(id_):
    try:
        with VnVFile.find(id_) as file:
            return render_template("files/file_browser.html", file=file)
    except Exception as e:
        print(e)
        return render_error(501, str(e))

@blueprint.route('/unittests/<int:id_>')
def unittesting(id_):
    try:
        with VnVFile.find(id_) as file:
            return render_template("files/unit_testing.html", file=file)
    except Exception as e:
        print(e)
        return render_error(501, str(e))

@blueprint.route('/comms/<int:id_>')
def comms(id_):
    try:
        with VnVFile.find(id_) as file:
            return render_template("files/comms.html", file=file)
    except Exception as e:
        print(e)
        return render_error(501, str(e))

@blueprint.route('/logs/<int:id_>')
def logs(id_):
    try:
        with VnVFile.find(id_) as file:
            return render_template("files/logs.html", file=file, proc=request.args.get("processor","-1"))
    except Exception as e:
        print(e)
        return render_error(501, str(e))

@blueprint.route('/processing/<int:id_>')
def processing(id_):
    try:
        with VnVFile.find(id_) as file:
            if file.isProcessing():
                return make_response("", 200)
            else:
                return make_response("", 201)
    except Exception as e:
        return make_response("", 501)


def unique_files():
    return [
        a for a in VnVFile.FILES.values()
    ]


def template_globals(globs):
    viewers.template_globals(globs)
    globs["files"] = VnVFile.FILES
    globs["uniquefiles"] = unique_files
    globs["list_registered_reports"] = list_registered_reports


def load_defaults(CONFIG, exclude):
    if exclude:
        VnVFile.delete_all()
    
    for key,value in CONFIG.items():
        VnVFile.add(key, value["filename"], value["reader"],  get_file_template_root(), value.get("config",{}))


def faker(PREFIX="../build"):
    VnVFile.add("Euler", "/home/ben/source/vv/vv-neams/build/examples/cpp/outputs/euler/out", "file",  get_file_template_root(), {})
    VnVFile.add("Heat", "/home/ben/source/vv/applications/heat/build/outputs/out", "file", get_file_template_root(), {})

    return
