import base64
import json
import os
import re
import uuid

import docutils.nodes

from sphinx.util import nested_parse_with_titles
from sphinx.util.docutils import SphinxDirective

from .viz.charts import VnVChartNode
from .dataclass import DataClass
from .jmes import jmes_jinja_query_str, jmes_jinga_stat,\
    jmes_jinja_codeblock, jmes_jinja_query, get_target_node, jmes_jinja_query_json

vnv_directives = {}
vnv_roles = {}

################ ADD A BUNCH OF ROLES TO TAKE STATISTICS OF JMES RESTULT #
def process_query(text, stats_function, tag="span"):
    html = f'''
                <{tag} data-o="on" 
                  data-f="{{{{data.getFile()}}}}" 
                  data-i="{{{{data.getAAId()}}}}" 
                  data-m="{stats_function}"
                  data-t="{tag}"
                  data-q="{base64.urlsafe_b64encode(text.encode('ascii')).decode('ascii')}">
                  {jmes_jinga_stat(text, stats_function)}
                </{tag}>
            '''
    return [VnVChartNode(html=html)], []


def get_stats_role(stats_function):
    def role(name, rawtext, text, lineno, inliner, options={}, content=[]):
        return process_query(text, stats_function)

    return role


class VnVProcessNode(docutils.nodes.General, docutils.nodes.Element):

    @staticmethod
    def visit_node(visitor, node):
        pass

    @staticmethod
    def depart_node(visitor, node):
        pass

VnVProcessNode.NODE_VISITORS = {
    'html': (VnVProcessNode.visit_node, VnVProcessNode.depart_node)
}


class VnVProcessDirective(SphinxDirective):
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}
    has_content = True

    def run(self):
        target, target_id = get_target_node(self)
        block = VnVProcessNode()
        nested_parse_with_titles(self.state, self.content, block)
        return [target, block]


class JmesStringDirective(SphinxDirective):
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}
    has_content = False

    def run(self):
        return process_query(" ".join(self.arguments), "str")



class JsonCodeBlockDirective(SphinxDirective):
    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        return process_query(" ".join(self.arguments), "codeblock", tag="div")


class JsonImageDirective(SphinxDirective):
    required_arguments = 1
    optional_arguments = 0
    file_argument_whitespace = True
    has_content = False
    option_spec = {
        "height": str,
        "width": str,
        "reader" : str
    }


    def process_condition(self):
        return re.sub('{{(.*?)}}', lambda x: jmes_jinja_query( x.group(1)), " ".join(self.arguments))


    script_template = '''
    <div id="{uid}" class="vnv_image" style="width:{width}; height:{height}; margin-left:auto; margin-right:auto;"></div>
    <script>
        $(document).ready(function(){{
            $.get("/files/render_file/{file}?filename={src}{reader}", function(data) {{
                $('#{uid}').html(data)
            }})
        }});
    </script>
    '''

    def getReader(self):
        r = self.options.get("reader")
        if r is not None:
            return "&reader=" + r
        return ""

    def getHtml(self, id_, content):
        return self.script_template.format(
            id_=id_,
            uid = uuid.uuid4().hex,
            height=self.options.get("height", "auto"),
            width=self.options.get("width", "auto"),
            src=content,
            reader=self.getReader(),
            file="{{data.file}}"
        )

    def run(self):
        j = self.process_condition()
        target, target_id = get_target_node(self)
        block = VnVChartNode(html=self.getHtml(target_id,  j))
        return [target, block]


class VnVBrowserDirective(SphinxDirective):
    required_arguments = 1
    optional_arguments = 0
    file_argument_whitespace = True
    has_content = False
    option_spec = {
        "height": str,
        "width": str,
    }

    script_template = '''
    <div class="vnv_image" style="width:{width}; height:{height}; margin-left:auto; margin-right:auto;">
     <iframe src='/browser?nohead=1&filename={file}' style="height:100%; width:100%; border:none;"></iframe>   
    </div>
    '''

    def getHtml(self, id_, content):
        return self.script_template.format(
            id_=id_,
            uid = uuid.uuid4().hex,
            height=self.options.get("height", "400px"),
            width=self.options.get("width", "100%"),
            file=" ".join(self.arguments)
        )

    def run(self):
        j = ""
        target, target_id = get_target_node(self)
        block = VnVChartNode(html=self.getHtml(target_id,  j))
        return [target, block]



class VnVCustomCodeDirective(SphinxDirective):
    required_arguments = 0
    optional_arguments = 0
    file_argument_whitespace = True
    has_content = True
    option_spec = {
        "height": str,
        "width": str,
    }

    script_template = '''
      <div class="vnv_code" style="width:{width}; height:{height}; padding:20px; background:black; color:white; border-radius:10px;">
        <pre style="color:white">{content}</pre>
      </div>
      '''

    def getHtml(self, id_):
        return self.script_template.format(
            id_=id_,
            uid = uuid.uuid4().hex,
            height=self.options.get("height", "auto"),
            width=self.options.get("width", "100%"),
            content="\n".join(self.content).strip()
        )

    def run(self):
        target, target_id = get_target_node(self)
        print(self.getHtml(target_id))
        block = VnVChartNode(html=self.getHtml(target_id))

        return [target, block]


class VnVHiveCodeDirective(SphinxDirective):
    required_arguments = 1
    optional_arguments = 0
    file_argument_whitespace = True
    has_content = False
    option_spec = {
        "height": str,
        "width": str,
        "block" : str
    }

    script_template = '''
    <div class="vnv_code" style="width:{width}; height:{height}; padding:20px; background:black; color:white; border-radius:10px; ">
      <pre style="color:white">{content}</pre>
    </div>
    '''

    def getHtml(self, id_):


        return self.script_template.format(
            id_=id_,
            uid = uuid.uuid4().hex,
            height=self.options.get("height", "auto"),
            width=self.options.get("width", "100%"),
            content=self.getContent()
        )

    def getContent(self):

        filename = os.path.expandvars(" ".join(self.arguments))
        if os.path.exists(filename):
            r = []
            start = False
            with open(filename) as f:
                for line in f.readlines():
                    if start == False:
                        if line.startswith("[" + self.options.get("block","Mesh") + "]"):
                            r.append(line)
                            start = True
                    else:
                        r.append(line)
                        if line.startswith("[]"):
                            return "\n".join(r).strip()

            return "Error: Could not find block"
        return "File Does not exist"

    def run(self):
        try:
            target, target_id = get_target_node(self)
            block = VnVChartNode(html=self.getHtml(target_id))
            return [target, block]
        except Exception as e:
            print(e)


vnv_directives["vnv-hive-code"] = VnVHiveCodeDirective
vnv_directives["vnv-code"] = VnVCustomCodeDirective
vnv_directives["vnv-file"] = VnVBrowserDirective
vnv_directives["vnv-image"] = JsonImageDirective
vnv_directives["vnv-print"] = JmesStringDirective
vnv_directives["vnv-process"] = VnVProcessDirective

vnv_roles["vnv"] = get_stats_role("str")
for f in DataClass.statsMethods:
    vnv_roles[f"vnv-{f}"] = get_stats_role(f)

def setup(sapp):
    sapp.add_node(VnVProcessNode, **VnVProcessNode.NODE_VISITORS)
    for key, value in vnv_roles.items():
        sapp.add_role(key, value)
    for key, value in vnv_directives.items():
        sapp.add_directive(key, value)