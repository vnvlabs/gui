
import json

from flask import render_template_string

from ..charts import JsonChartDirective
from sphinx.directives import optional_int
from ...jmes import jmes_jinja_query_json, register_context

try:
    the_app
except NameError:
    the_app = None


class TableChartDirective(JsonChartDirective):

    script_template = '''
        {{% with current_id = data.getRandom() %}}
        <div id="{{{{current_id}}}}">  
             <h4 class="vnv-table-title"></h4>
             <div class="{id_} vnv-table" width="100%" height="100%"></div>
             <script>
                 ( () => {{
                     const parent =$('#{{{{current_id}}}}')
                     url = "/directives/updates/{uid}/{{{{data.getFile()}}}}/{{{{data.getAAId()}}}}?context=quick-table"
                     update_now(url, 3000, function(config) {{
                         if (config["errors"]) {{
                            parent.find(".vnv-table").html(config["errors"])
                         }} else {{
                            var table = new Tabulator(parent.find(".vnv-table")[0], config);
                            parent.find(".vnv-table-title").html(config["title"] || "VnV Quick Table")
                        }}
                    }})
                 }})()
             </script>
        </div>
        {{%endwith%}}

         '''

    def register(self):
        return self.getContent()


class QuickTableChartDirective(TableChartDirective):
    required_arguments = 0
    optional_arguments = 0
    file_argument_whitespace = True
    has_content = False
    option_spec = {
        "names": str,
        "fields": str,
        "data": str,
        "title": str
    }

    @staticmethod
    def quick_table_post_process(text, data, file):
            try:
                options = json.loads(render_template_string(text, data=data, file=file))
            except Exception as e:
                return {"errors": str(e)}

            names = options.get("names")
            fields = options.get("fields")
            data = options.get("data")

            return  {
                      "layout" : "fitData",
                      "data" : data,
                      "columns": [
                          { "title" : names[i] , "field" : fields[i]} for i in range(0,len(names))
                      ]
                }

    def getContext(self):
        return "?context=quick-table"

    def getRawContent(self):
        title = self.options.get("title","VnV Table")
        return f"""{{
          "names" : {self.options.get("names","[]")},
          "fields" : {self.options.get("fields","[]")},
          "data" : {self.options.get("data","[]")},
          "title" : {json.dumps(title)}
        }}
        """

def setup(sapp):
    global the_app
    the_app = sapp

    sapp.add_directive("vnv-table",TableChartDirective)
    sapp.add_directive("vnv-quick-table", QuickTableChartDirective)

register_context("quick-table", QuickTableChartDirective.quick_table_post_process)
