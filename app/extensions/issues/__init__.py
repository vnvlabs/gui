import json

from flask import request, make_response, Blueprint

from app.models.VnVInputFile import VnVInputFile


def GET_DEFAULT_ISSUES():
    return "[]"


class ISSUES_INFO:
    def __init__(self, defs):
        self.issues = GET_DEFAULT_ISSUES() if "issues" not in defs else json.dumps(defs["issues"])
        self.issues_enabled =  defs.get("issues_enabled", True)

    def toJson(self):
        return {"issues" : self.issues, "issues_enabled" : self.issues_enabled}

    def fromJson(self,j):
        if "issues" in j:
            self.issues = j["issues"]
        if "issues_enabled" in j:
            self.issues_enabled = j["issues_enabled"]

    def fullInputFile(self, j):
        if self.issues_enabled:
            if "actions" not in j:
                j["actions"] = {}
            j["actions"]["VNV:issues"] = json.loads(self.issues)

    def get(self):
        return self.issues

    def tablist(self):
        return {"issues" : ["Issues", "issues/issues.html"]}

blueprint = Blueprint(
        'issues',
        __name__,
        template_folder='templates',
        url_prefix="/issues"
)
@blueprint.route('/save-issues', methods=["POST"])
def save():
    try:
        id_ = request.args.get("fileId")
        with VnVInputFile.find(id_) as file:
            if "data" in request.args:
                try:
                    a = json.loads(request.args["data"])
                    file.extra["issues"].issues = json.dumps(a)
                    return make_response("", 200)
                except:
                    return make_response("", 201)
            return make_response("", 202)
    except:
        return make_response("", 203)


@blueprint.route('/toggle_issues', methods=["POST"])
def toggle():
    try:
        id_ = request.args.get("fileId")
        with VnVInputFile.find(id_) as file:
            file.extra["issues"].issues_enabled = not file.extra["issues"].issues_enabled
            return make_response("show" if file.extra["issues"].issues_enabled else "hide", 200)
    except:
        return make_response("", 203)



def init_issues_info(file,name,path,defs,plugs):
    return ISSUES_INFO(defs)

VnVInputFile.EXTRA_TABS["issues"] = init_issues_info
