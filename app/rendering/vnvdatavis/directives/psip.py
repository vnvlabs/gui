import json

from sphinx.util.docutils import SphinxDirective

from .viz.charts import VnVChartNode
from .jmes import get_target_node


class PSIPDirective(SphinxDirective):

    required_arguments = 1
    optional_arguments = 0
    file_argument_whitespace = True
    has_content = False
    option_spec = {
        "height": str,
        "width": str,
        "class" : str
    }

    def register(self):
        return None

    def getScript(self): return self.script_template

    def getHtml(self):

        return f'''
          <div class="{self.options.get("class","")}" style="width:{self.options.get("width","100%")}; height:{self.options.get("height" , "100%")};">
               {{%with initial_data= data.query_json('{" ".join(self.arguments)}'), readonly=True %}}
               
               {{%include 'psip/selfaccess.html'%}}
               <script>
                  a = {{{{initial_data|safe}}}}
                  set_psip_data(a,-1)
               </script>      
               {{%endwith%}} 
         </div>
        '''

    def run(self):
        target, target_id = get_target_node(self)
        block = VnVChartNode(html=self.getHtml())
        return [target, block]


    def register(self):
        return self.getContent()


def setup(sapp):
    sapp.add_directive("vnv-psip", PSIPDirective)
