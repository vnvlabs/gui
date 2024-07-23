import os
import json
import time

vnv_plugins = {}
vnv_reports = {}
vnv_executables = {}
vnv_last = [0]

def load_registrations():
#Load the users home registration file.
    curr_time = time.time()
    if curr_time - vnv_last[0] < 20:
        return
    try:
        vnv_reports.clear()
        vnv_executables.clear()
        vnv_plugins.clear()

        global_reg_file = os.path.expanduser("~/.vnv")
        with open(global_reg_file,'r') as f:
            reg = json.load(f)

            #Process all the files that have been added
            for name, value in reg.get("executables",{}).items():
                filename = value["filename"]
                pd = os.path.dirname(filename)
                full_filename =  os.path.join(pd, os.path.expandvars(filename))
                vnv_executables[name] = {
                    "filename": full_filename,
                    "description": value.get("description", "No Description Available"),
                    "package": name,
                    "defs" : value.get("defs",{})
                }

            for name, value in reg.get("plugins",{}).items():
                vnv_plugins[name] = value

            for name, value in reg.get("reports",{}).items():
                vnv_reports[name] = value

        vnv_last[0] = time.time()
    except:
       pass

def list_vnv_executables():
    load_registrations()
    a = [[k, v["description"], v["package"]] for k, v in vnv_executables.items()]
    a.append(["Custom", "Enter path to executable manually","custom"])
    return a


def list_registered_reports():
    return vnv_reports

def list_vnv_plugins():
    return vnv_plugins
