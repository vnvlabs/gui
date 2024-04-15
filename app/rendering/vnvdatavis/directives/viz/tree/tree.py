import hashlib
import os
import re
import uuid

import docutils
from docutils.nodes import SkipNode
from sphinx.util.docutils import SphinxDirective
from ..charts import JsonChartDirective

from ..jmes import get_target_node, jmes_jinja_query


try:
    the_app
except NameError:
    the_app = None



class TreeChartDirective(JsonChartDirective):
    script_template = '''
        <div>
        <div id="{id_}" class='vnv_jsonviewer' width="100%" height="100%"></div>
        <script>
           const element = $(document.currentScript).parent().find('.vnv_jsonviewer)  
           var data = JSON.parse(`{config}`);
           var tree = new JSONFormatter(data['data'], true ,data['config']);
           element.appendChild(tree.render());
           
           url = "/directives/updates/{uid}/{{{{data.getFile()}}}}/{{{{data.getAAId()}}}}"
           update_now(url, 3000, function(config) {{
                var data = JSON.parse(config);
                var tree = new JSONFormatter(data['data'], true ,data['config']);
                element.clear()
                element.appendChild(tree.render());
           }});    
           
        </script></div> '''

    def register(self):
        return self.getContent()

def setup(sapp):
    global the_app
    the_app = sapp
    sapp.add_directive("vnv-tree",TreeChartDirective)
