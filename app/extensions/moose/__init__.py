import glob
import json
import os.path
import subprocess
import uuid

from flask import request, make_response, Blueprint, jsonify

from app.models.VnVInputFile import VnVInputFile

#This is going to be the moose extension for the VnV code.
#We are going to add:
    # MOOSE File Tab in the input files view

def GET_DEFAULT_MOOSE(filename):
    dirname = os.path.dirname(filename)
    files = glob.glob(os.path.join(dirname,"*.i"))
    if len(files) > 0:
        with open(files[0],'r') as f:
            return f.read()

    return '''

[Mesh]
  # We use a pre-generated mesh file (in exodus format).
  # This mesh file has 'top' and 'bottom' named boundaries defined inside it.
  file = mug.e
[]

[Variables]
  [./diffused]
    order = FIRST
    family = LAGRANGE
  [../]
[]

[Kernels]
  [./diff]
    type = Diffusion
    variable = diffused
  [../]
[]

[BCs]
  [./bottom] # arbitrary user-chosen name
    type = DirichletBC
    variable = diffused
    boundary = 'bottom' # This must match a named boundary in the mesh file
    value = 1
  [../]

  [./top] # arbitrary user-chosen name
    type = DirichletBC
    variable = diffused
    boundary = 'top' # This must match a named boundary in the mesh file
    value = 0
  [../]
[]

[Executioner]
  type = Steady
  solve_type = 'PJFNK'
  file_base = 'out'
[]

[Outputs]
  execute_on = 'timestep_end'
  exodus = true
[]
'''

def extract_moose_schema(filename):
    a = subprocess.check_output(["./ex01-opt", "--json"], timeout=10).decode('ascii')
    akey = "**START JSON DATA**"
    ekey = "**END JSON DATA**"
    start_pos = a.find(akey) + len(akey)
    end_pos = a.find(ekey)
    return json.loads(a[start_pos:end_pos])

def verify_moose_input(filename):
    a = subprocess.check_output(["./ex01-opt", "--check-input","-i",filename], timeout=10).decode('ascii')
    akey = "*** ERROR ***"
    aind = a.find(akey)
    if aind >= 0:
        return 2, a[aind + len(akey):]

    akey = "*** WARNING ***"
    aind = a.find(akey)
    if aind >= 0:
        return 1, a[aind + len(akey):]

    return 0, "Syntax Ok"


class MOOSE_INFO:
    def __init__(self, file : VnVInputFile, defs):
        self.application = file.filename
        self.filename = os.path.join(os.path.dirname(self.application),f"input-{uuid.uuid4().hex[0:8]}.i")
        self.text = None
        if "inputfile" in defs:
            try:
                with open(defs["inputfile"], 'w') as f:
                    self.set(f.read())
            except:
                pass

        if self.text is None:
            self.set(GET_DEFAULT_MOOSE(self.application))

        self.schema = extract_moose_schema(self.application)

    def set(self,data):
        self.text = data
        with open(self.filename, 'w') as f:
            f.write(self.text)

    def toJson(self):
        return {"text": self.text}

    def fromJson(self, j):
        if "text" in j:
            self.set(j["text"])

    def fullInputFile(self, j):
        pass # Dont put anything in the moose input file

    def get(self):
        return self.text

    def tablist(self):
        return {"moose": ["Moose Input File", "moose/moose.html"]}

    def autocomplete(self):
        return []

blueprint = Blueprint(
    'moose',
    __name__,
    template_folder='templates',
    url_prefix="/moose"
)




@blueprint.route('/save/<int:fileId>', methods=["POST"])
def save(fileId):

    try:
        data = request.args.get("data")
        with VnVInputFile.find(fileId) as file:
            moose_info = file.extra["moose"]
            moose_info.set(data)

            return make_response("", 200)
    except:
        return make_response("", 203)


@blueprint.route('/get/<int:fileId>', methods=["GET"])
def get(fileId):
    try:
        with VnVInputFile.find(fileId) as file:
            moose_info = file.extra["moose"]
            return make_response(moose_info.text, 200)
    except Exception as e:
        return make_response("Could Not Load File", 203)

@blueprint.route('/load/<int:fileId>', methods=["POST"])
def load(fileId):

    try:
        filename = request.args.get("filename")
        with VnVInputFile.find(fileId) as file:
            moose_info = file.extra["moose"]
            with open(filename,'w') as f:
                moose_info.set( f.read() )
            return make_response("", 200)
    except:
        return make_response("", 203)


@blueprint.route('/autocomplete/<int:fileId>', methods=["GET"])
def autocomplete(fileId):
    row = int(request.args.get("row"))
    col = int(request.args.get("col"))
    prefix = request.args.get("prefix")
    data = request.args.get("data")

    try:
        with VnVInputFile.find(fileId) as file:
            moose_info = file.extra["moose"]
            a = moose_info.autocomplete(data)
            return make_response(jsonify(a),200)
    except:
        return make_response([], 203)



@blueprint.route('/annotate/<int:fileId>', methods=["GET"])
def annotate(fileId):
    data = request.args.get("data")

    try:
        with VnVInputFile.find(fileId) as file:
            moose_info = file.extra["moose"]
            moose_info.set(data)
            ok, msg = verify_moose_input(moose_info.filename)
            if ok > 0:
                a = [{
                    "row": 1,
                    "column": 1,
                    "text": msg,
                    "type": 'error' if ok == 2 else "warning",
                    "source": 'vnv'}
                ]
            else:
                a = []

            return make_response(jsonify(a),200)
    except:
        return make_response("", 203)

def init_moose_info(file, name, path, defs, plugs):
    try:
        return MOOSE_INFO(file,defs)
    except Exception as e:
        print("not a moose application")
        return None # must not be a moose application.

VnVInputFile.EXTRA_TABS["moose"] = init_moose_info
