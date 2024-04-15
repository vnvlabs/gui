
import json
from ..charts import JsonChartDirective
from sphinx.directives import optional_int
from ...jmes import jmes_jinja_query_json

try:
    the_app
except NameError:
    the_app = None


class TableChartDirective(JsonChartDirective):
    script_template = '''
         <div>
         <div class="{id_} vnv-table" width="100%" height="100%"></div>
         <script>
             const parent = $(document.currentScript).parent()
             const obj = JSON.parse(`{config}`)
             var table = new Tabulator(parent.find("vnv-table")[0], obj);
         
             url = "/directives/updates/{uid}/{{{{data.getFile()}}}}/{{{{data.getAAId()}}}}"
             update_now(url, 3000, function(config) {{
                 var table = new Tabulator(parent.find("vnv-table")[0], JSON.parse(config));
            }})
         </script>
         </div>
         '''

    def register(self):
        return self.getContent()



def jmes_query(x):
    return x


def json_array(x):
    return json.loads(x)


class QuickTableChartDirective(TableChartDirective):
    required_arguments = 0
    optional_arguments = 0
    file_argument_whitespace = True
    has_content = False
    option_spec = {
        "width": optional_int,
        "height": optional_int,
        "names": json_array,
        "fields": json_array,
        "data": jmes_query,
        "title": str
    }

    def columns(self):
        names = self.options.get("names", [])
        fields = self.options.get("fields", [])

        r = []
        for n, i in enumerate(names):
            r.append(f'''{{title:"{i}", field:"{fields[n]}"}}''')

        return ",".join(r)

    def register(self):
        return jmes_jinja_query_json(self.options.get("data", "`[]`"))

    def getHtml(self, id_, uid):
        return f'''
         <div>
         <div class='card' style='padding:20px;'>
            <div id="v-{id_}" class='vnv-table' width="{self.options.get("width", 400)}" height="{self.options.get("height", 400)}"></div>
         </div>   
         <script>
              
              const p = document.currentScript();
              
              $(document).ready(function() {{
                
                var jqid = $(document.currentScript).parent()                
                var table = new Tabulator(jqid, {{
                      layout : "fitDataStretch",
                      "title" : "{self.options.get("title", "VnV Table")}",
                      "columns": [{self.columns()}]
                }});
                
                var url = "/directives/updates/{uid}/{{{{data.getFile()}}}}/{{{{data.getAAId()}}}}"
                update_now(url, 3000, function(config) {{
                  table.setData(JSON.parse(config))
                }})
                
            }})
            </script>
            </div>
            '''


class DataTableChartDirective(TableChartDirective):
    required_arguments = 0
    optional_arguments = 0
    file_argument_whitespace = True
    has_content = False
    option_spec = {
        "width": str,
        "height": str,
        "query": str,
        "title": str
    }

    def register(self):
        return self.getContent()

    def getRawContent(self):
        return json.dumps(self.options)

    def register(self):
        return jmes_jinja_query_json(self.options.get("data", "`[]`"))

    def getHtml(self, id_, uid):
        return f'''
         <div class='card' style='padding:20px;'>
            <div id="{uid}" 
                 class='vnv-table' 
                 style="width:{self.options.get("width", "auto")};height:{self.options.get("height", "auto")}">
            </div> 
         </div>   
          <script>
             var jqid = $(document.currentScript).parent()                
             var table = new Tabulator(jqid, {{
                      layout : "fitDataStretch",
                      "title" : "{self.options.get("title", "VnV Table")}",
                      "columns": [{self.columns()}]
             }});

             var url = "/directives/updates/{uid}/{{{{data.getFile()}}}}/{{{{data.getAAId()}}}}"
             update_now(url, 3000, function(config) {{
                table.setData(JSON.parse(config))
             }})

            </script>
            '''


def setup(sapp):
    global the_app
    the_app = sapp

    sapp.add_directive("vnv-table",TableChartDirective)
    sapp.add_directive("vnv-quick-table", QuickTableChartDirective)
    sapp.add_directive("vnv-data-table",DataTableChartDirective)
