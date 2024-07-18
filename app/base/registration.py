import os
import json

vnv_plugins = {}
vnv_reports = {}

vnv_executables = {
    "Custom" : {
        "filename": "",
        "description": "Custom Path",
        "package": ""
    }
}

def load_registrations():
#Load the users home registration file.
    global_reg_file = os.path.expanduser("~/.vnv")
    try:
     with (open(global_reg_file,'r') as f):
        reg = json.load(f)

        #Process all the files that have been added
        for name, value in reg.get("executables",{}).items():
            filename = value["filename"]
            pd = os.path.dirname(filename)
            full_filename =  os.path.join(pd, os.path.expandvars(filename))
            vnv_executables[name] = {
                "filename": full_filename,
                "description": value.get("description", "No Description Available"),
                "package": name
            }

        for name, value in reg.get("plugins",{}).items():
            vnv_plugins[name] = value

        for name, value in reg.get("reports",{}).items():
            vnv_reports[name] = value

    except:
        pass

def list_vnv_executables():
    load_registrations()
    return [[k, v["description"], v["package"]] for k, v in vnv_executables.items()]


def list_registered_reports():
    return vnv_reports

def list_vnv_plugins():
    return vnv_plugins
