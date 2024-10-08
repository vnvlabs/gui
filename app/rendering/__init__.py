import json
import os
import shutil
import subprocess
import sys
import textwrap
import uuid

import sphinx.cmd.build

from app import Directory

conf_template = '''
import sys

{SYSPATHS}

project = "VNV"
copyright = f"2021, VNV"
author = "VNV"
release = "VNV"
extensions = {extensions}
vnv_file={fileId}
update_dir="{updateDir}"

html_theme = "faketheme"
html_theme_path = ["{path}"]
exclude_patterns = ['_build']
html_static_path = ['_static']

'''

EXTS = ["sphinx.ext.mathjax", "vnvdatavis"]
PATHS = [os.path.abspath(os.path.join('app', 'rendering'))]

def add_custom_vnv_directive(filepath, module_name):
    PATHS.append(filepath)
    EXTS.append(module_name)


def get_conf_template(fileId):

    syspaths = [
        "sys.path.append(\"" + p + "\")" for p in PATHS
    ]
    return conf_template.format(fileId=fileId, extensions=EXTS, SYSPATHS="\n".join(syspaths), updateDir=Directory.UPDATE_DIR, path=os.path.abspath(os.path.join('app', 'rendering')))


def setup_build_directory(src_dir, fileId):
    os.makedirs(os.path.join(src_dir, "_build"))
    os.makedirs(os.path.join(src_dir, "_static"))
    os.makedirs(os.path.join(src_dir, "_templates"))

    # Write a configuration file in the source directory.
    with open(os.path.join(src_dir, "conf.py"), 'w') as w:
        w.write(get_conf_template(fileId))

    # Override the template with a simple template that just shows the body.


# files dict ( type -> package -> name -> template


class TemplateBuild:
    def __init__(self, src_dir, id_, descrip=None, smap = {}):
        self.src_dir = os.path.basename(src_dir)
        self.root_dir = src_dir
        self.file = id_
        self.descrip = descrip
        self.smap = smap
        self.codeblocks = None

    def read(self, f):
        try:
          with open(os.path.join(self.root_dir, f), 'r') as ff:
            r = ff.readlines()
            return "".join(r)
        except:
            return ""
        
    def get_code_block(self,codeblock):
        if self.codeblocks is None:
           
           try:
             with open(os.path.join(self.root_dir,"codeblocks.json")) as f:
                self.codeblocks = json.load(f)
           except:
                self.codeblocks = {}
                
        return self.codeblocks.get(codeblock , "<error>")

    def getSourceMap(self,package, name):
        return self.smap.get(package + ":"+name,{})

    def get_title(self,type, package, name, short=False):
        tt = "short" if short else "title"
        return os.path.join("renders",self.src_dir, "_build", "html",
               f"{type}_{package}_{name}_{tt}.html")


    def get_type_description(self, type, package, name):
        if self.descrip is None:
           try:
             with open(os.path.join(self.root_dir, "descriptions.json"), 'r') as w:
                self.descrip = json.load(w)
           except:
                self.descrip = {}
        return self.descrip.get(type, {}).get(package + ":" + name)

    def get_html_file_name(self, type, package, name):
        return os.path.join(
            "renders",
            self.src_dir,
            "_build",
            "html",
            f"{type}_{package}_{name}.html")

    def get_action(self, package, name):
        return self.get_html_file_name("Actions", package, name)

    def get_job_creator(self, package, name):
        return self.get_html_file_name("Workflows", package, name)

    def get_job_creator_job(self, package, name, jobName):
        return os.path.join("renders", self.src_dir, "_build", "html",
                            f"Workflow_Job_{package}_{name}_{jobName}.html")

    def get_raw_job_creator_job(self, package, name, jobName):
        return self.read(f"Workflow_Job_{package}_{name}_{jobName}.rst")

    def get_raw_job_creator(self, package, name):
        return self.read(f"Workflows_{package}_{name}.rst")

    def get_unit_test_test_content(self, package, name, test):
        return os.path.join("renders", self.src_dir, "_build", "html", f"UnitTest_Test_{package}_{name}_{test}.html")

    def render_temp_string(self, content):

        temp_dir = os.path.join(self.root_dir, "temp")
        if not os.path.exists(temp_dir):
            setup_build_directory(temp_dir, self.file)

        with open(os.path.join(temp_dir, "index.rst"), 'w') as w:
            w.write(content)

        params = ["-M", "html", temp_dir, os.path.join(temp_dir, "_build")]
        sphinx.cmd.build.make_main(params)
        return os.path.join("renders", self.src_dir, "temp", "_build", "html", "index.html")

    def render_to_string(self, content):

        temp_dir = os.path.join(self.root_dir, uuid.uuid4().hex)
        setup_build_directory(temp_dir, self.file)

        with open(os.path.join(temp_dir, "index.rst"), 'w') as w:
            w.write(content)

        params = ["-M", "html", temp_dir, os.path.join(temp_dir, "_build")]
        sphinx.cmd.build.make_main(params)

        with open(os.path.join(temp_dir, "_build", "html", "index.html"), 'r') as w:
            va = w.read()

        shutil.rmtree(temp_dir)
        return va

    def get_raw_rst(self, data):
        usage = data.getUsageType()
        if usage == "Internal":
            return None  # not supported yet -- internal test doesn't know what ip it belongs to.
        elif usage == "Package":
            fname = f"Options_{data.getPackage()}.rst"
        elif usage == "Root":
            fname = "Introduction.rst"
        else:
            fname = f"{usage}s_{data.getPackage()}_{data.getName()}.rst"

        return self.read(fname)

    def get_unit_test_test_raw(self, package, name, test):
        return os.path.join("renders", self.src_dir, "_build", "html", f"UnitTest_Test_{package}_{name}_{test}.html")

    def get_raw_introduction(self):
        return self.read("Introduction.rst")

    def get_raw_conclusion(self):
        return self.read("Conclusion.rst")

    def get_raw_package(self, package):
        return self.read(f"Options_{package}.rst")

    def get_package(self, package):
        return os.path.join(
            "renders",
            self.src_dir,
            "_build",
            "html",
            f"Options_{package}.html")

    def get_assets_directory(self):
        return os.path.join(
            "renders",
            self.src_dir,
            "_build",
            "html",
            "static")

    def get_introduction(self):
        return os.path.join(
            "renders",
            self.src_dir,
            "_build",
            "html",
            "Introduction.html")

    def get_intro_title(self, short = False):
        t = "short" if short else "title"
        return os.path.join(
            "renders",
            self.src_dir,
            "_build",
            "html",
            f"Introduction_{t}.html")

    def get_conclusion(self):
        return os.path.join(
            "renders",
            self.src_dir,
            "_build",
            "html",
            "Conclusion.html")

    def get_file_description(self, package, name):
        return self.get_html_file_name("Files", package, name)


def build(src_dir, templates, id_):
    setup_build_directory(src_dir, id_)
    fnames = []
    descriptions = {}
    codeblocks = {}
    sourcemap = {}

    for type_, packages in templates.items():
        if type_ in ["Introduction", "Conclusion"]:
            fnames.append(f"{type_}.rst")
            with open(os.path.join(src_dir, fnames[-1]), 'w') as w:
                w.write(f'{textwrap.dedent(packages["docs"]["template"])}\n\n')
            fnames.append(f"{type_}_short.rst")

            with open(os.path.join(src_dir, fnames[-1]), 'w') as w:
                w.write(f'{textwrap.dedent(packages["docs"].get("shortTitle",""))}\n\n')
            fnames.append(f"{type_}_title.rst")

            with open(os.path.join(src_dir, fnames[-1]), 'w') as w:
                w.write(f'{textwrap.dedent(packages["docs"].get("title",""))}\n\n')

        elif type_ in ["CodeBlocks"]:
            codeblocks = packages;


        elif type_ in ["Options"]:
            for package, docinfo in packages.items():
                fnames.append("Options_" + package + ".rst")
                with open(os.path.join(src_dir, fnames[-1]), 'w') as w:
                    w.write(f'\n\n{textwrap.dedent(docinfo["docs"]["template"])}\n\n')

        else:
            for package, point in packages.items():
                name_package = package.split(":")

                #Write the template file
                fnames.append(f"{type_}_{name_package[0]}_{name_package[1]}.rst")

                with open(os.path.join(src_dir, fnames[-1]), 'w') as w:
                    if len(point["docs"]) == 0 or len(point["docs"]["template"]) == 0 :
                        w.write(f"")
                    else:
                        w.write(f"\n{textwrap.dedent(point['docs']['template'])}\n\n")

                #Write the title file
                fnames.append(f"{type_}_{name_package[0]}_{name_package[1]}_title.rst")
                with open(os.path.join(src_dir, fnames[-1]), 'w') as w:
                    if len(point["docs"]) == 0:
                        w.write(f"")
                    else:
                        w.write(f"\n{textwrap.dedent(point['docs']['title'])}\n\n")

                #Write the short title.
                fnames.append(f"{type_}_{name_package[0]}_{name_package[1]}_short.rst")
                with open(os.path.join(src_dir, fnames[-1]), 'w') as w:
                    if len(point["docs"]) == 0:
                        w.write(f"")
                    else:
                        w.write(f"\n{textwrap.dedent(point['docs'].get('shortTitle','Hello There :vnv:`Id`'))}\n\n")

                descriptions.setdefault(type_, {})[name_package[0] + ":" + name_package[1]] = point["docs"]

                if type_ == "UnitTests":
                    tests = point["tests"]
                    for test in tests.keys():
                        fnames.append(f"UnitTest_Test_{name_package[0]}_{name_package[1]}_{test}.rst")
                        with open(os.path.join(src_dir, fnames[-1]), 'w') as w:
                            if len(tests[test]) == 0:
                                w.write(f"\n\n\n\n")
                            else:
                                w.write(f"\n{textwrap.dedent(tests[test])}\n\n")

                elif type_ == "Workflows":
                    tests = point["jobs"]
                    for test in tests.keys():
                        fnames.append(f"Workflow_Job_{name_package[0]}_{name_package[1]}_{test}.rst")
                        with open(os.path.join(src_dir, fnames[-1]), 'w') as w:
                            if len(tests[test]) == 0:
                                w.write(f"\n\n\n\n")
                            else:
                                w.write(f"\n{textwrap.dedent(tests[test]['template'])}\n\n")

                elif type_ == "InjectionPoints":

                    smap = {}
                    for stage,sinfo in point["stages"].items():
                        smap[stage] = { "filename" : sinfo["info"]['filename'], "lineNumber" : sinfo["info"]["lineNumber"] }
                    sourcemap[package] = smap

    index = '''.. toctree::\n\t:maxdepth: 22\n\t:caption: Contents:\n\n\t{files}\n\n'''.format(
        files="\n\t".join(fnames))
    with open(os.path.join(src_dir, "index.rst"), 'w') as w:
        w.write(index)

    with open(os.path.join(src_dir, "descriptions.json"), 'w') as w:
        json.dump(descriptions, w)

    with open(os.path.join(src_dir, "codeblocks.json"), 'w') as w:
        json.dump(codeblocks, w)

    with open(os.path.join(src_dir, "runv.py"), 'w') as w:
        w.write(
            f'''import os\nimport sphinx.cmd.build\nsphinx.cmd.build.make_main(["-M","html","{src_dir}",os.path.join("{src_dir}","_build")])''')
    try:

        a = subprocess.run([sys.executable, os.path.join(src_dir, "runv.py")])
    except Exception as e:
        print(e)
    return TemplateBuild(src_dir, id_, descrip=descriptions, smap=sourcemap)


def render_rst_to_string(content):

    temp_dir = os.path.join(Directory.VNV_TEMP_TEMP_PATH, uuid.uuid4().hex)
    setup_build_directory(temp_dir, -1)

    with open(os.path.join(temp_dir, "index.rst"), 'w') as w:
        w.write(textwrap.dedent(content))

    params = ["-M", "html", temp_dir, os.path.join(temp_dir, "_build")]
    sphinx.cmd.build.make_main(params)

    with open(os.path.join(temp_dir, "_build", "html", "index.html"), 'r') as w:
        va = w.read()

    shutil.rmtree(temp_dir)
    return va
