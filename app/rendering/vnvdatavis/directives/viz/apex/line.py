import json

from sphinx.errors import ExtensionError

from ..charts import JsonChartDirective, VnVChartNode
from ...jmes import jmes_jinja_query, get_target_node, jmes_jinja_query_json, \
    jmes_check, jmes_jinja_zip, jmes_jinja_query_join, jmes_jinja_query_str_array
from .apex import ApexChartDirective


def jmes_expression(x):
    return x


def lineareabar(x):
    if x in ['line', 'area', 'bar', 'column']:
        return x
    raise ExtensionError("Invalid type")

def json_jmes_array(a):
    aa = json.loads(a)
    if not isinstance(aa, list):
        raise ExtensionError("Not a json array")
    for i in aa:
        if not isinstance(i, str) or not jmes_check(i):
            raise ExtensionError("Invalid Jmes String")
    return aa


def json_array(a):
    aa = json.loads(a)
    if not isinstance(aa, list):
        raise ExtensionError("Not a json array")
    for i in aa:
        if not isinstance(i, str):
            raise ExtensionError("Invalid Jmes String")
    return aa


def jmes_check_local(text):
    if jmes_check(text):
        return text
    raise ExtensionError("Invalid Jmes")

def jmes_array_str(text):
    # Could be a string or, it could be an array of jmes stuff
    return text


def jmes_array_str_array(text):
    try:
        a = json.loads(text)
        if isinstance(a,list):
            for i in a:
                jmes_array_str(i)
            return text

    except:
        pass

    raise ExtensionError("Invalid Jmes Array Str Array")




class ApexLineChartDirective(ApexChartDirective):
    required_arguments = 0
    optional_arguments = 0
    file_argument_whitespace = True
    has_content = False
    option_spec = {
        'yaxis': str,
        'xaxis': str,
        'title': str,
        'label': str,
        "type": lineareabar
    }

    def getRawContent(self):
        return f'''
        {{
            "series": [{{
                "name": "{self.options.get('label', "Series")}",
                "type": "{self.options.get("type", "area")}",
                "data": {self.options.get('yaxis', '[1,1,2,3,5]')}
            }}],
            "chart": {{
                "width" : "100%",
                "height" : "100%",
                "type": "{self.options.get("type", "area")}",
                "zoom": {{
                    "enabled": true 
                }}
            }},
            "dataLabels": {{
                "enabled": false
            }},
            "stroke": {{
                "curve": "smooth"
            }},
            "plotOptions": {{
                "bar": {{
                    "columnWidth": "50%"
                }}
            }},
            "title": {{
                "text": "{self.options.get('title', 'Line Chart')}",
                "align": "left"
            }},
            "grid": {{
                "row": {{
                    "colors": ["#f3f3f3", "transparent"],
                    "opacity": 0.5
                }}
            }},
            "xaxis": {{
                "categories": {self.options.get('xaxis', '["a","b","c","d","e"]')}
            }}
        }}
        '''



def setup(sapp):
    sapp.add_directive("vnv-scatter", ApexLineChartDirective)


