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
from app.moose import py as pyhit, find_moose_executable_recursive, get_suggestions


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


SAVED_SCHEMA = {}


class HiveFile():

    def extract_moose_schema(self, filename, **kwargs):

        if filename is None:
            return {}, "No Schema Provided"
        elif filename in SAVED_SCHEMA and "reload" not in kwargs:
            return SAVED_SCHEMA[filename], ""

        elif not os.path.exists(filename):
            return {}, "Executable does not exist"

        try:
            args = kwargs.get("args",["--json"])
            cwd = kwargs.get("cwd", os.path.dirname(filename))
            a = subprocess.check_output([filename] + args, cwd=cwd, timeout=10).decode('ascii')
            akey = "**START JSON DATA**"
            ekey = "**END JSON DATA**"
            start_pos = a.find(akey) + len(akey)
            end_pos = a.find(ekey)
            SAVED_SCHEMA[filename] = json.loads(a[start_pos:end_pos])
            return SAVED_SCHEMA[filename], "Schema Loaded Successfully"

        except Exception as e:
            print(e)
            return {}, "Error: " + str(e)

    def __init__(self, filename, **kwargs):
        self.uuid = uuid.uuid4().hex
        self.filename = filename
        self.moose_executable = kwargs.get("moose-exe", find_moose_executable_recursive(os.path.dirname(filename)))
        if self.moose_executable is None:
            self.moose_executable = os.path.join(os.path.dirname(filename),os.path.splitext(os.path.basename(filename))[0] + "-opt")
        self.schema, self.error = self.extract_moose_schema(self.moose_executable, **kwargs)
        self.cwd = os.path.dirname(filename)

    def set_schema(self, exe, **kwargs):
        self.moose_executable = exe
        self.schema, self.error = self.extract_moose_schema(self.moose_executable, **kwargs)
        return self.error
   
    def read(self):
        with open(self.filename, 'r') as f:
            return f.read()

    def format(self, text):
        return pyhit.load(text).format()
    
    
    def save(self, text):
        try:
            with open(self.filename, 'w') as f:
                f.write(text)
                return {"success" : "true"}
        except Exception as e:
            return {"failure" : str(e)}

    def regenerate_mesh(self, text):
        try:
            with open(os.path.join(self.cwd, f"{self.uuid}.i"),'w') as f:
                f.write(text)

            a = subprocess.run([self.moose_executable, "-i", f"{self.uuid}.i", "--mesh-only"], cwd=self.cwd, timeout=10, capture_output=True)
            mfile = os.path.join(self.cwd, f'{self.uuid}_in.e')
            if a.returncode == 0 and os.path.exists(mfile):
                return f"/pv?file={os.path.join(self.cwd, f'{self.uuid}_in.e')}" ,200
        except Exception as e:
            print(e)
            pass

        return "mesh generation failed", 201
    
    def validate(self, text):
        try:
            with open(os.path.join(self.cwd, f"{self.uuid}.i"), 'w') as f:
                f.write(text)
            a = subprocess.run([self.moose_executable, "-i", f"{self.uuid}.i", "--check-input","--color","off"], cwd=self.cwd, capture_output=True, timeout=10)
            stdout = a.stdout.decode("ascii")
            stderr = a.stderr.decode("ascii")
            if a.returncode == 0:
                aa = stdout.find("*** WARNING ***")
                if aa > 0:
                    return [{"row": 0, "column": 1, "text": stdout[aa:], "type": 'warning',"source": 'vnv'}]
                return []
            else:

                start = stderr.find("*** ERROR ***")
                end = stderr.find("Stack Frames")
                if end < 0:
                    end = len(stderr)

                mess = stderr[start:end]
                return [{"row": 0, "column": 1, "text": mess, "type": 'error',"source": 'vnv'}]

        except Exception as e:
            print("HERE")
            return [{"row": 0, "column": 1, "text": "Validation Failed:" + str(e), "type": 'warning', "source": 'vnv'}]

    def autocomplete(self, text, row, col, prefix):
        return moose_autocomplete(text,row,col,prefix)
        
        return [{"caption": "TODO", "value": "TODO", "meta": "", "desc": "HIVE (moose) Autocomplete is under active development"}]

SAVED_HIVE_FILES = {}


def render_hive(filename, **kwargs):
    try:
        hive = HiveFile(filename,**kwargs)
        SAVED_HIVE_FILES[hive.uuid] = hive
        return render_template("browser/hive.html", hive=hive)

    except Exception as e:

        return render_code(filename, **kwargs)

def get_hive_file(uuid):
    return SAVED_HIVE_FILES.get(uuid)


FILE_READERS = {
    "image": render_image,
    "html": render_html,
    "paraview": render_paraview,
    "csv": render_csv,
    "code": render_code,
    "markdown": render_markdown,
    "rst": render_rst,
    "json": render_json,
    "hive" : render_hive
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
