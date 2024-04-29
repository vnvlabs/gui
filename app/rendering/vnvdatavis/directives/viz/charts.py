import hashlib
import os
import re
import uuid

import docutils
from docutils.nodes import SkipNode
from sphinx.util.docutils import SphinxDirective

from ..jmes import get_target_node, jmes_jinja_query

class VnVChartNode(docutils.nodes.General, docutils.nodes.Element):

    @staticmethod
    def visit_node(visitor, node):
        visitor.body.append(node["html"])
        raise SkipNode

    @staticmethod
    def depart_node(visitor, node):
        pass


VnVChartNode.NODE_VISITORS = {
    'html': (VnVChartNode.visit_node, VnVChartNode.depart_node)
}

try:
    the_app
except NameError:
    the_app = None


class JsonChartDirective(SphinxDirective):
    registration = {}
    required_arguments = 0
    optional_arguments = 0
    file_argument_whitespace = True
    has_content = True
    option_spec = {
        "height": str,
        "width": str,
        "class": str
    }

    def getRawContent(self):
        return "\n".join(self.content)

    def register(self):
        return None

    def getScript(self):
        return self.script_template

    def getContent(self):
        return re.sub('{{(.*?)}}', lambda x: jmes_jinja_query( x.group(1)),self.getRawContent())

    def getHtml(self, id_, uid):
        return f'''
          <div class="{self.options.get("class", "")}" style="width:{self.options.get("width", "100%")}; height:{self.options.get("height", "100%")};">{self.getScript().format(
            id_=id_,
            config=self.getContent(),
            uid=uid
        )}</div>
        '''

    def get_update_dir(self):
       return the_app.config.update_dir


    def updateRegistration(self):
        r = self.register()
        if r is not None:
            uid = hashlib.md5(r.encode()).hexdigest()
            if not os.path.exists(uid):
                with open(os.path.join(self.get_update_dir(), uid), 'w') as f:
                    f.write(r)
            return uid
        return -1

    def run(self):
        uid = self.updateRegistration()
        target, target_id = get_target_node(self)
        block = VnVChartNode(html=self.getHtml(uuid.uuid4().hex[0:5], uid))
        return [target, block]


    def register(self):
        return self.getContent()




def setup(sapp):
    global the_app
    the_app = sapp
    sapp.add_node(VnVChartNode, **VnVChartNode.NODE_VISITORS)
