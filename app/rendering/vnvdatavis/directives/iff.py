import hashlib
import json
import os
import re
import uuid

import docutils
import flask
from docutils.nodes import SkipNode
from sphinx.directives import optional_int
from sphinx.util import nested_parse_with_titles
from sphinx.util.docutils import SphinxDirective

from .jmes import get_target_node, jmes_jinja_query, jmes_jinja_if_query, register_context

vnv_directives = {}


class VnVIfNode(docutils.nodes.General, docutils.nodes.Element):

    @staticmethod
    def visit_node(visitor, node):
        visitor.body.append(f'''
                    {{% with current_id = data.getRandom() %}}
                    <div id="{{{{current_id}}}}">  

            <div class="node_start" hidden ></div>
            <div class="node_end" hidden ></div>
            <script>
                       ( () => {{
            var jqobj = $('#{{{{current_id}}}}')
               
            url = "/directives/updates/{node["uid"]}/{{{{data.getFile()}}}}/{{{{data.getAAId()}}}}?context=if"
             
            update_now(url, 1000, function(config) {{
                    var nodes = jqobj.find('node_start') 
                    var nodee = jqobj.find('node_end')[0]
                    while (nodes.next()[0] != nodee) {{ nodes.next().remove(); }}
                    nodes.after(config)  
            }})
               }})()
            </script>
          </div>
          {{%endwith%}}
        ''')

    @staticmethod
    def depart_node(visitor, node):
        pass


VnVIfNode.NODE_VISITORS = {
    'html': (VnVIfNode.visit_node, VnVIfNode.depart_node)
}


class VnVIfDirective(SphinxDirective):
    required_arguments = 1
    optional_arguments = 0
    file_argument_whitespace = True
    has_content = True

    def get_json(self):
        return { "condition" : " ".join(self.arguments), "content" : "\n".join(self.content) }

    @staticmethod
    def post_process(cont, data, file):
        j = json.loads(cont)

        if data.query(j["condition"]):
            tname = file.render_to_string(j["content"])
            return flask.render_template_string(tname, data=data, file=file)
        return ""

    def run(self):
        cont = json.dumps(self.get_json())
        uid = hashlib.md5(cont.encode()).hexdigest()
        with open(os.path.join(the_app.config.update_dir, uid),'w') as f:
            f.write(cont)

        target, target_id = get_target_node(self)
        block = VnVIfNode(uid=uid)
        return [target, block]


vnv_directives["vnv-if"] = VnVIfDirective

try:
    the_app
except NameError:
    the_app = None


def setup(sapp):
    global the_app
    the_app = sapp

    sapp.add_node(VnVIfNode, **VnVIfNode.NODE_VISITORS)

    print(the_app.config.update_dir)

    for key, value in vnv_directives.items():
        sapp.add_directive(key, value)

register_context("if", VnVIfDirective.post_process)
