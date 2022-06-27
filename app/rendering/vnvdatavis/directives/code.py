import base64
import json
import os
import re
import uuid

import docutils.nodes

from sphinx.util import nested_parse_with_titles
from sphinx.util.docutils import SphinxDirective

from .charts import VnVChartNode
from .dataclass import DataClass
from .jmes import jmes_jinja_query_str, jmes_jinga_stat, \
    jmes_jinja_codeblock, jmes_jinja_query, get_target_node, jmes_jinja_query_json

vnv_directives = {}
vnv_roles = {}



class VnVCodeDirective(SphinxDirective):
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        "title" : str
    }
    has_content = True

    def get_title(self):
        if "title" in self.options:
            return f"""<h6 style="margin-left:6px; >{self.options.get("title")}</h6>"""
        return ""

    def run(self):
        target, target_id = get_target_node(self)
        cont = "\n".join(self.content)

        html = f"""
               <div class="card" style="margin:10px; padding:10px;">
                 {self.get_title()}
                 {{{{ file.render_code_block("{self.arguments[0]}") | safe }}}}
               </div>"""
        return [target, VnVChartNode(html=html)]

def setup(sapp):
    sapp.add_directive("vnv-code-block", VnVCodeDirective)
