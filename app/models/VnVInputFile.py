import json
import os
import textwrap
import uuid

import flask
import jsonschema
from ansi2html import Ansi2HTMLConverter
from flask import jsonify
from jsonschema.exceptions import ErrorTree, ValidationError, SchemaError

from app.base.utils import mongo
from app.models import VnV
from app.models.VnVConnection import VnVLocalConnection, VnVConnection, connectionFromJson
from app.models.json_heal import autocomplete
from app.rendering import render_rst_to_string
from app.rendering.vnvdatavis.directives.dataclass import DataClass


def get_current_path(newVal, row, col):
    i = 0
    while i < len(newVal):
        c = newVal[i]
        if c in map:
            looking = map[c]


def get_row_and_column(path, newVal, a):
    try:
        if len(path) == 0:
            return 1, 1
        p = a
        while len(path) > 1:
            p = p[path.popleft()]
        p[path.pop()] = "91123212"
        aa = json.dumps(a, separators=(',', ':')).find("91123212")

        s = newVal.split("\n")
        newlines = 0
        currcol = 0
        inquotes = False
        for i in newVal:
            sub = True
            currcol += 1
            if i == "\n":  # new line so reset col count and currcol
                sub = False
                newlines += 1
                currcol = 0
            elif i == " " and not inquotes:
                sub = False
            elif i == "\"" and (i == 0 or newVal[i - 1] != "\\"):
                inquotes = not inquotes
            if sub: aa -= 1
            if aa == 0: return newlines, currcol;
    except:
        pass

    return 1, 1


class Dependency:
    def __init__(self, remoteName=None, type=None, describe="", **kwargs):
        self.id_ = uuid.uuid4().hex
        self.remoteName = remoteName
        self.type = type
        self.desc = describe
        self.kwargs = kwargs

    def to_json(self):
        return {"id": self.id_, "type": self.type, "remoteName": self.remoteName, "desc": self.desc,
                "kwargs": self.kwargs}

    def describe(self):
        if len(self.desc) > 0:
            return self.desc

        if self.type in ["text"]:
            return "A " + self.type + " based input file (" + self.kwargs.get("text")[0:50] + "...)"
        elif self.type == ["upload"]:
            return f" A File uploaded from your local machine (" + self.kwargs.get("original", "None") + ")"
        else:
            return "A " + self.type + " of remote file \"" + self.kwargs.get("text", "") + "\""

    @staticmethod
    def from_json(j):
        d = Dependency()
        d.id_ = j["id"]
        d.remoteName = j["remoteName"]
        d.type = j["type"]
        d.desc = j.get("desc", "")
        d.kwargs = j["kwargs"]
        return d




class VnVInputFile:
    COUNTER = 5000

    FILES = {}

    DEFAULT_SPEC = {}

    EXTRA_TABS = {}

    def tablist(self):
       try:

            a = {
            #! "exec": ["Execution Configuration", "inputfiles/execute.html"],
            "description" : ["About", "inputfiles/about.html"],
            "inputfile": ["VnV Input File", "inputfiles/input.html"],
            "browse": ["Browse", "files/file_browser.html"],
            }

            for k,v in self.extra.items():
              if v is not None:
                for kk,vv in v.tablist().items():
                    a[kk] = vv

            a["jobs"] =["Results", "inputfiles/jobs.html"]
            return a
       except Exception as e:
           print("HEy YO ", e)
           return {}

    def __init__(self, name, path=None):
        
        self.name = name
        self.displayName = name
        self.filename = path if path is not None else "path/to/application"

        self.icon = "icon-box"
        self.id_ = VnVInputFile.get_id()
        self.connection = VnVLocalConnection()

        self.loadfile = ""
        self.additionalPlugins = {}

        self.spec = "{}"
        self.specLoad = {}

        self.execFile = ""
        self.specValid = False
        self.desc = None
        self.rendered = None
        self.specDump = "${application}"
        self.plugs = {}

        # Update my specification -- based on the input file.
        self.updateSpec()

        #Get the default as defined in the specification which was loaded on the prev line
        defs = self.get_executable_defaluts()

        # Set the execution file
        if "empty_exec" in defs and defs["empty_exec"]:
            execObj = {}
        else:
            execObj = self.defaultExecution()
            
        if "exec" in defs:
            for key, value in defs["exec"].items():
                execObj[key] = value
        
        #self.exec = json.dumps(execObj, indent=4)

        self.extra = {}


        # Set the default Input file values.
        if "input" in defs:
            jsoninput = defs["input"]
        else:
            jsoninput = VnV.getVnVConfigFile_1()
        
        jsoninput["execution"] = execObj        
        self.value = json.dumps(jsoninput, indent=4)
        
        for k, v in VnVInputFile.EXTRA_TABS.items():
            self.extra[k] = v(self, name, path, defs, defs.get("plugs",{}))

        if "plugins" in defs and isinstance(defs["plugins"],dict):
            self.plugs = defs["plugins"]

        self.updateSpec()
            

    def toJson(self):
        a = {}
        a["name"] = self.name
        a["displayName"] = self.displayName
        a["filename"] = self.filename
        a["icon"] = self.icon
        a["connection"] = self.connection.toJson()
        a["loadfile"] = self.loadfile
        a["value"] = self.value
        a["spec"] = self.spec
        a["specDump"] = self.specDump
        a["specValid"] = self.specValid
        a["execFile"] = self.execFile
        a["plugs"] = self.plugs
        a["rendered"] = self.rendered

        a["extra"] = {}
        for k,v in self.extra.items():
            a["extra"][k] = v.toJson()

        return a

    def browse(self):
        import os
        from app.models.readers import LocalFile
        return LocalFile(os.path.dirname(self.filename), self.id_, self.connection, reader="directory")


    @staticmethod
    def fromJson(a):
        r = VnVInputFile(a["name"])
        r.filename = a["filename"]
        r.icon = a["icon"]
        r.displayName = a.get("displayName", r.name)  # backwards compat
        r.connection = connectionFromJson(a["connection"])
        r.loadfile = a["loadfile"]
        r.value = a["value"]
        r.spec = a["spec"]
        r.specDump = a["specDump"]
        r.specValid = a["specValid"]
        r.rendered = a["rendered"]
        r.execFile = a["execFile"]
        r.plugs = a["plugs"]

        for k,v in r.extra.items():
            v.fromJson(a["extra"][k])

        try:
            r.specLoad = json.loads(r.spec)
        except:
            r.specLoad = VnVInputFile.DEFAULT_SPEC.copy()

        return r

    def setConnection(self, hostname, username, password, port):
        if isinstance(self.connection, VnVConnection):
            self.connection.connect(username, hostname, port, password)
        else:
            self.connection = VnVConnection()
            self.connection.connect(username, hostname, int(port), password)

    def setConnectionLocal(self):
        if not isinstance(self.connection, VnVLocalConnection):
            self.connection = VnVLocalConnection()
        self.connection.connect("", "", "", "")

    def setFilename(self, fname, specDump, plugs):
        try:
            self.plugs = json.loads(plugs)
            self.filename = fname
            self.specDump = specDump
            self.updateSpec()
            return True
        except:
            return False

    def plugs_str(self):
        return json.dumps(self.plugs, indent=4)

    def getFileStatus(self):
        if self.connection.connected():
            if self.connection.exists(self.filename):
                if (self.specValid):
                    return ["green", "Valid"]
                else:
                    return ["blue", "Could not extract schema. See specification tab for more information!"]
            else:
                return ["#d54287", "Application does not exist"]
        else:
            return ["red", "Connection is not open"]

    # When user clicks save we save the input and update the plugins.
    # if auto is on, we should also update the specification.
    def saveInput(self, newValue):
        self.value = newValue

    def validateInput(self, newVal):
        try:
            a = json.loads(newVal)
            jsonschema.validate(a, schema=self.specLoad)
            return []
        except ValidationError as v:
            r, c = get_row_and_column(v.path, newVal, a)
            return [{"row": r, "column": c, "text": v.message, "type": 'warning', "source": 'vnv'}]
        except Exception as e:
            return [{"row": 1, "column": 1, "text": str(e), "type": 'warning', "source": 'vnv'}]

    def schema(self):
        return self.spec



    def updateSpec(self):
        self.specValid = False
        self.rendered = None
        self.specLoad = {"error": "No specification available"}
        self.spec = json.dumps(self.specLoad)

        if not self.connection.connected():
            self.specLoad["error-reason"] = "Disconnected"
            self.spec = json.dumps(self.specLoad, indent=4)
            return

        def getSpecDumpCommand(inputfilename):
            main = self.specDump.replace("${application}", self.filename)
            main = main.replace("${inputfile}", inputfilename)
            return main

        try:
            s = {"additionalPlugins": self.plugs}
            s["schema"] = {"dump": True, "quit": True}
            path = self.connection.write(json.dumps(s), None)
            aa = getSpecDumpCommand(path)
            res = self.connection.execute(aa, env={**os.environ, "VNV_INPUT_FILE": path})
            a = res.find("===START SCHEMA DUMP===") + len("===START SCHEMA DUMP===")
            b = res.find("===END SCHEMA_DUMP===")
            
            if a > 0 and b > 0 and b > a:
                #read the spec
                self.spec = res[a:b]
                #parse the spec
                self.specLoad = json.loads(self.spec)
                #add our execution spec
                self.specLoad["properties"]["execution"] = VnVInputFile.getExecutionSchema()
                #dump the spec to get back to string
                self.spec = json.dumps(self.specLoad, indent=4)
                #update some other stuff. 
                self.specValid = True
                self.rendered = self.get_executable_description()
            else:
                self.specLoad["error-message"] = res
                self.specLoad["error-command"] = aa
                self.specLoad["error-input"] = s
                self.specLoad["error-input-file-name"] = path
                self.spec = json.dumps(self.specLoad, indent=4)

        except Exception as e:
            self.specLoad["error-exception"] = str(e)
            self.spec = json.dumps(self.specLoad, indent=4)

    NO_INFO = "No Application Information Available\n===================================="

    def get_executable_description_(self):
        if self.specLoad is not None:
            desc = self.specLoad.get("definitions", {}).get("executable", {})
            return desc.get("template", self.NO_INFO) if desc is not None else self.NO_INFO

        else:
            return self.NO_INFO
        
    def get_executable_defaluts(self):
        if self.specLoad is not None:
            return self.specLoad.get("definitions", {}).get("executable", {}).get("default",{})
        return {}
    
    VNVINPUTFILEDEF = 1022334234443

    def get_executable_description(self):
        if self.rendered is None:
            self.rendered = flask.render_template_string(render_rst_to_string(self.get_executable_description_()),
                                                         file=self, data=DataClass(self, self.id_, 1022334234443))
        return self.rendered

    def getId(self):
        return self.id_


    def describe(self):
        return f'{self.connection.describe()}:/{self.filename}'

    def execTemplate(self):
        return self.exec

    # TODO Implement this.
    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "shell": {"type": "string", "enum": ["bash"]},
            "shebang": {"type": "string"},
            "working-directory": {"type": "string"},
            "vnv": {"type": "boolean"},
            "environment": {
                "type": "object"
            },
            "mpi" : {
              "type" : "object",
              "properties" : {
                  "on" : { "type" : "boolean", "default" : False },
                  "processors" : { "type" : "integer" , "default" : 1},
                  "runner" : {"type" : "string", "default" : "mpirun"},
                  "extra-args" : {"type" : "string"}
              }  
            },
            "executioner" : {
                "type" : "object",
                "properties" : {
                  "name" : { 
                      "type" : "string" ,
                      "enum" : [ "bash" , "slurm" ],
                      "default" : "bash"
                  }
                }  
            },
            "vnv-input-file": {"type": "string"},
            "command-line": {"type": "string",
                             "description": "Command to submit with input file called '${inputfilename}'"},
            "input-staging": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["cp", "mv", "slink", "hlink"]},
                        "source": {"type": "string"},
                        "dest": {"type": "string"}
                    },
                    "required": ["action", "source", "dest"]
                }
            },
            "output-staging": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["cp", "cp -r", "mv", "ln", "ln -s"]},
                        "source": {"type": "string"},
                        "dest": {"type": "string"}
                    },
                    "required": ["action", "source", "dest"]
                }
            }

        },
        "additionalProperties": False
    }

    EXECUTION_SCHEMA = None

    VNV_PREFIX = ""

    @staticmethod
    def getExecutionSchema():
        if VnVInputFile.EXECUTION_SCHEMA is None:
            VnVInputFile.EXECUTION_SCHEMA = json.loads(json.dumps(VnVInputFile.CONFIG_SCHEMA))
            VnVInputFile.EXECUTION_SCHEMA["properties"]["active_overrides"] = {"type": "array",
                                                                               "items": {"type": "string"}}
            VnVInputFile.EXECUTION_SCHEMA["properties"]["overrides"] = {
                "type": "object",
                "additionalProperties": json.loads(json.dumps(VnVInputFile.CONFIG_SCHEMA))
            }

        return VnVInputFile.EXECUTION_SCHEMA

    def defaultExecution(self):
        return {
        "vnv": True,
        "shell": "bash",
        "working-directory": "${application_dir}",
        "environment": {},
        "mpi" : { "on" : False, "processors" : 1},
        "vnv-input-file": "GUI",
        "input-staging": [],
        "output-staging": [],
        "command-line": "${application}",
        "name": self.name,
        "active_overrides": [],
        "overrides": {}
    }

    def autocomplete_input(self, row, col, pre, val):
        return autocomplete(val, self.specLoad, int(row), int(col), plugins=self.plugs)

    def autocomplete_spec(self, row, col, pre, val):
        return []

    def refresh_job(self, jobId):
        j = self.connection.get_job(jobId)
        if j is not None:
            return j.refresh()
        return {"stdout": "unknown job", "errorcode": 100}

    def get_jobs(self):
        return [a for a in self.connection.get_jobs()]

    def fullInputFile(self):
        j = json.loads(self.value)
        if "actions" not in j:
            j["actions"] = {}

        for k,v in self.extra.items():
            v.fullInputFile(j)

        return json.dumps(j, indent=4)

    
    def execute(self, val = None):
        if val is None:
            val = self.value

        inp_dir = json.loads(val).get("job", {}).get("dir", "/tmp")

        workflow_id = uuid.uuid4().hex
        script, name = self.script(val, workflow_id)

        meta = {
            "vnv_input": self.fullInputFile(),
            "workflow_id": workflow_id,
            "workflow_dir": inp_dir
        }

        return self.connection.execute_script(script, name=name, metadata=meta)


    def script(self, val, workflowId):
        inputfile = json.loads(val)
        data = inputfile.get("execution",{})
        for i in data.get("active_overrides", []):
            if i in data.get("overrides", {}):
                over = data["overrides"][i]
                for k, v in over.items():
                    data[k] = v

        script = bash_script(self.filename, self.fullInputFile(), data, workflowName=workflowId)
        return script, data.get("name")

    @staticmethod
    def get_id():
        VnVInputFile.COUNTER += 1
        return VnVInputFile.COUNTER

    @staticmethod
    def add(name, path=None, defs={}, plugs={}):

        a = mongo.loadInputFile(name)
        if a is not None:
            raise Exception("Name is taken")
        else:
            f = VnVInputFile(name, path=path)

        VnVInputFile.FILES[f.id_] = f
        return f

    @staticmethod
    def load(name):
        a = mongo.loadInputFile(name)
        if a is not None:
            f = VnVInputFile.fromJson(a)
            VnVInputFile.FILES[f.id_] = f
            return f

    @staticmethod
    def loadAll():
        for a in mongo.list_input_files():
            f = VnVInputFile.fromJson(a)
            VnVInputFile.FILES[f.id_] = f

    @staticmethod
    def removeById(fileId):
        a = VnVInputFile.FILES.pop(fileId)
        mongo.deleteInputFile(a.name)

    @staticmethod
    def delete_all():
        for k, v in VnVInputFile.FILES.items():
            mongo.deleteInputFile(v.name)
        VnVInputFile.FILES.clear()

    @staticmethod
    def find(id_):
        if id_ in VnVInputFile.FILES:
            return VnVInputFile.FileLockWrapper(VnVInputFile.FILES[id_])
        raise FileNotFoundError

    class FileLockWrapper:
        def __init__(self, file):
            self.file = file

        def __enter__(self):
            return self.file

        def __exit__(self, type, value, traceback):
            mongo.persistInputFile(self.file)


def njoin(array):
    return "\n".join(array)




def get_bash_header(application_path, data, workflowName):
    
    inputfilename = data.get("vnv-input-file") if data.get("vnv-input-file","GUI") not in ["","GUI"] else ".vnv-input-${VNV_WORKFLOW_ID}"
    add_inputfile = "" if data.get("vnv-input-file") == None else f"export VNV_INPUT_FILE={inputfilename}"
    
    return textwrap.dedent(f"""
    {data.get("shebang", "#!/usr/bin/bash")}
    export application={application_path}
    export application_dir=$(dirname {application_path})
    export VNV_WORKFLOW_ID={workflowName}
    {add_inputfile}
    cd {data.get("working-directory", "${application_dir}")}"""
    )

def get_bash_environment(data):
    return njoin(["export " + k + "=" + v for k, v in data.get("environment", {})])

def get_bash_inputstaging(data):
    return njoin([a["action"] + " " + a["source"] + " " + a["dest"]] for a in data.get("input-staging", {}))

def get_bash_commandline(data):
    command_line = data.get("command-line", "echo 'No Command line provided'")
    
    mpi = data.get("mpi",{})
    if mpi.get("on",False):     
        return f"""{mpi.get("runner","mpirun")} -n {mpi.get("processors",1)} {mpi.get("extra-args","")} {command_line}"""
    
    return command_line 

def get_bash_outputstaging(data):
    return njoin([a["action"] + " " + a["source"] + " " + a["dest"]] for a in data.get("output-staging", {}))
    

def get_bash_write_inputfile(data, inputfile):
    if data.get("vnv-input-file","GUI") in ["GUI",""]:
       return textwrap.dedent(f'''
        \ncat << EOF > ${{VNV_INPUT_FILE}}
            {inputfile}
        \nEOF\n''') 
    
    return ""


def bash_script(application_path, inputfile, data, workflowName):

    script = textwrap.dedent(f"""

    {get_bash_header(application_path, data, workflowName)}
    {get_bash_write_inputfile(data, inputfile)}
    {get_bash_environment(data)}
    {get_bash_inputstaging(data)}
    {get_bash_commandline(data)}
    {get_bash_outputstaging(data)}""")
    
    return script
