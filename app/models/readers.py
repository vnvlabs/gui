import csv
import datetime
import hashlib
import json
import os
import subprocess
import urllib.request
import uuid
from pathlib import Path

import docutils
import markdown as markdown
import flask
import pygments
from flask import render_template, make_response, jsonify
from pygments.lexers import guess_lexer_for_filename

from app import Directory


def getPath(filename, exten=None):
    uu = hashlib.sha1(filename.encode()).hexdigest()
    if exten is None:
        ext = filename.split(".")
        if len(ext) > 1:
            uu += "." + ext[-1]
    else:
        uu += "." + exten

    d = Directory.STATIC_FILES_DIR
    p = os.path.join(d, uu)
    return p, uu


def getUID(filename, exten=None):
    p, uu = getPath(filename, exten=exten)
    if not os.path.exists(p):
        os.symlink(filename, p)
    return uu


def render_image(filename, **kwargs):
    return f"<img class='card' src='/temp/files/{getUID(filename)}' style='max-width:100%;'>"


def render_html(filename, **kwargs):
    return f"<iframe class='card' src='/temp/files/{getUID(filename)}' style='width: 100%;height:80vh;'>"


def render_pdf(filename, **kwargs):
    return f"<iframe class='card' src='/temp/files/{getUID(filename)}' style='width: 100%;height:80vh;'>"


def render_paraview(filename, **kwargs):
    return f"<iframe class='card' src='/pv?file={filename}' style='width: 100%;height:80vh;'>"


def render_vti(filename, **kwargs):
    path = urllib.request.pathname2url(f"/temp/files/{getUID(filename)}")
    return f"<iframe class='card' src='/static/volume/index.html?fileURL={path}' style='width: 100%;height:80vh;'>"


def render_rst(filename, **kwargs):
    with open(filename, 'r') as f:
        d = f.read()
    p, u = getPath(filename, exten="html")

    with open(p, "w") as ff:
        ff.write(docutils.core.publish_string(d, writer_name='html5').decode())

    return f"<iframe src='/static/files/{u}' style='width: 100%;height:80vh;'>"


def render_markdown(filename, **kwargs):
    with open(filename, 'r') as f:
        return f"<div>{markdown.markdown(f.read())}</div>"


def render_code(filename, **kwargs):
    with open(filename, 'r') as f:
        return render_template("browser/ace.html", TEXT=f.read(), filename=filename)


def render_csv(filename, **kwargs):
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        return render_template("csv/template.html", RAWDATA=json.dumps([r for r in reader]))


def json_to_jstree_json(j):
    def get_json_obj(key, value):

        valstr = ""
        if not (isinstance(value, dict) or isinstance(value, list)):
            valstr = str(value)

        children = []
        if isinstance(value, dict):
            children = [get_json_obj(k, v) for k, v in value.items()]
        elif isinstance(value, list):
            children = [get_json_obj(str(k), v) for k, v in enumerate(value)]

        print(value.__class__.__name__, icon_map)

        return {
            "text": f"{key}: {valstr}",
            "icon": f" feather icon-{icon_map.get(value.__class__.__name__, 'minus')}",
            "state": {
                "opened": True,
                "disabled": False,
                "selected": False,
            },
            "children": children
        }

    return [get_json_obj(k, v) for k, v in j.items()]


def render_json(filename, **kwargs):
    with open(filename, 'r') as f:
        reader = json.load(f)
        return render_template("browser/json.html", RAWDATA=json.dumps(json_to_jstree_json(reader)))

FILE_READERS = {
    "image": render_image,
    "html": render_html,
    "paraview": render_paraview,
    "csv": render_csv,
    "code": render_code,
    "markdown": render_markdown,
    "rst": render_rst,
    "json": render_json
}

EXT_MAP = {
    ".jpeg": "image",
    ".jpg": "image",
    ".png": "image",
    ".gif": "image",
    ".svg": "image",
    ".md": "markdown",
    ".e": "paraview",
    ".json": "json",
    ".i" : "hive"
}


def get_reader(reader, ext):
    if reader is not None:
        return reader

    if ext in EXT_MAP:
        return EXT_MAP[ext]

    elif ext[1:] in FILE_READERS:
        return ext[1:]

    return "code"


def has_reader(reader):
    return reader in FILE_READERS


icon_map = {
    dict.__name__: "folder",
    list.__name__: "list",
    bool.__name__: "check",
    str.__name__: "type"
}


class LocalFile:
    def __init__(self, abspath, vnvfileid, connection, reader=None, **kwargs):

        self.inputpath = abspath

        self.vnvfileid = vnvfileid
        self.connection = connection
        self.setInfo()
        self.reader = get_reader(reader, self.ext)

        self.breadcrumb = None
        self.iconStr = None
        self.exists_ = None
        self.children_ = None
        self.download_ = None
        self.is_dir_ = None
        self.root_ = None
        self.options = kwargs

    def render_reader(self):
        if self.reader is not None:
            reader_func = FILE_READERS.get(self.reader)
            if reader_func is not None:
                return reader_func(self.download(), **self.options)
        return "<div> Reader is not implemented yet. Sorry</div>"

    def setHighlightLines(self, hl_lines):
        self.highlight = hl_lines

    def has_option(self, key):
        return key in self.options

    def get_option(self, key, default=None):
        return self.options.get(key, default)

    def setInfo(self):
        self.abspath, self.dir, self.name, self.ext, self.size, self.lastMod, self.lastModStr = self.connection.info(
            self.inputpath)

    def getVnVFileId(self):
        return self.vnvfileid

    def url(self):
        return urllib.request.pathname2url(self.abspath)

    def is_dir(self):
        if self.is_dir_ is None:
            self.is_dir_ = self.connection.is_dir(self.abspath)
        return self.is_dir_

    def connected(self):
        return self.connection.connected()

    def exists(self):
        if self.exists_ is None:
            self.exists_ = self.connection.exists(self.abspath)
        return self.exists_

    def children(self):
        if self.children_ is None:
            self.children_ = [LocalFile(i, self.vnvfileid, self.connection) for i in
                              self.connection.children(self.abspath)]
            self.children_.sort(key=lambda x: x.name)
        return self.children_

    def download(self):
        if self.download_ is None:
            self.download_ = self.connection.download(self.abspath)
        return self.download_

    def render(self, modal=""):

        if self.is_dir():
            return render_template("browser/directory.html", file=self, modal=modal)

        try:
            return self.render_reader()
        except Exception as e:
            return f"<div>{str(e)}</div>"

    def icon(self):
        return "folder" if self.is_dir() else "file"

    def crumb(self):
        if self.breadcrumb is None:
            cc = self.connection.crumb(self.dir)
            self.breadcrumb = [LocalFile(i, self.vnvfileid, self.connection) for i in cc]
            self.breadcrumb.append(self)
        return self.breadcrumb

    def root(self):
        if self.root_ is None:
            self.root_ = self.connection.root()
        return self.root_
