import json
import os.path
import uuid

import jsonschema
from flask import render_template_string
from sphinx.errors import ExtensionError

from ..charts import JsonChartDirective
from collections.abc import MutableMapping

from ...jmes import register_context


def dict_pop(d):

    if isinstance(d,dict):
        pops = []
        for k,v in d.items():
            if isinstance(v, dict) and "kind" in v:
                pops.append(k)
            else:
                dict_pop(v)
        for i in pops:
            d.pop(i)

    elif isinstance(d,list):
        pops = []
        for v in d:
            if isinstance(v, dict) and "kind" in v:
                pops.append(v)
            else:
                dict_pop(v)
        for i in pops:
            d.remove(i)

try:
    apex_schema
except:
    with open(os.path.join(os.path.dirname(__file__), "apex-schema.json")) as f:
        apex_schema = json.load(f)
    dict_pop(apex_schema)

def apex_post_process(text, data, file, schema = apex_schema):
  try:
    # Extract all the trace definitions -- trace.x = scatter trace.y = line
    # Turn it into an object
    rdata = {}
    try:
        options = json.loads(render_template_string(text,data=data,file=file))
    except Exception as e:
        return {"errors" : str(e) }
    if schema:
        try:
            jsonschema.validate(options,schema)
        except Exception as e:
            return {"errors" :  str(e) }

    return options

  except Exception as e:
      print(e)

class ApexOptionsDict(MutableMapping):
    """A dictionary that calls a function when a requested key does not
    exist in the dictionary"""

    def __init__(self):
        self.store = {
            "height": str,
            "width": str,
        }

    def __getitem__(self, key):
        if key in self.store:
            return self.store[key]
        return str

    def __setitem__(self, key, value):
        self.store[key] = value

    def __delitem__(self, key):
        del self.store[key]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)


loading = {
    "series": [70],
    "chart": {
          "height": 350,
          "type": "radialBar",
    },
    "plotOptions": {
      "radialBar": {
         "hollow": {
            "size": "70%",
         }
      },
    },
    "labels": ["Loading"],
}

class ApexChartDirective(JsonChartDirective):
    script_template = '''
                   {{% with current_id = data.getRandom() %}}
                    <div id="{{{{current_id}}}}">  

    
               
               <div class='main-div vnv-table'></div> 
               <div class="card error-message-div" style="border:1px solid red; display:none; margin:20px; padding=20px; z-index:1000; "></div>   
             
             
                <script>
                               ( () => {{
                    const parent = $('#{{{{current_id}}}}')
                    var chart = new ApexCharts(parent.find('.main-div')[0], {loading});
                    chart.render();
                    
                    url = "/directives/updates/{uid}/{{{{data.getFile()}}}}/{{{{data.getAAId()}}}}{context}"
                    update_now(url, 1000, function(config) {{
                        
                        if (config["errors"]) {{
                            parent.find('.errors-div').show()   
                            parent.find('.error-message-div').html(config["errors"])
                            parent.find('.error-message-div').show()
                            parent.find('.main-div').hide()
                        
                        }} else {{
                            parent.find('.main-div').show()
                            parent.find('.errors-div').hide()   
                            chart.updateOptions(config) 
                        }}
                    }})
                    
                   }})()
                </script>
                
          </div>           {{%endwith%}}

        '''

    def getContext(self):
        return "?context=apex"

    def getLoading(self):
        return loading

    def getHtml(self, id_, uid):
        return f'''
          <div class="{self.options.get("class", "")}" style="width:{self.options.get("width", "100%")}; height:{self.options.get("height", "100%")};">{self.getScript().format(
            id_=id_,
            config=self.getContent(),
            uid=uid,
            uid1=uuid.uuid4().hex,
            loading=json.dumps(loading),
            context=self.getContext()
        )}</div>
        '''

    def register(self):
        return self.getContent()



class ApexDirec(ApexChartDirective):
    required_arguments = 0
    optional_arguments = 0
    file_argument_whitespace = False
    has_content = False
    option_spec = ApexOptionsDict()

    #Use the options instead of raw json
    def getRawContent(self):
        return json.dumps(self.options)


def setup(sapp):
    sapp.add_directive("vnv-apex", ApexDirec)
    sapp.add_directive("vnv-apex-raw", ApexChartDirective)

register_context("apex", apex_post_process)
