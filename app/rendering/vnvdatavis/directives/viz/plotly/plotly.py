import json
import os.path

import flask
from flask import render_template_string
from sphinx.errors import ExtensionError

from ..charts import JsonChartDirective
from collections.abc import MutableMapping

import math
import numpy as np
import json

from ...fakejmes import jmespath_autocomplete
from ...jmes import register_context


def gen_comp(cap, val, type, desc):
    return {"caption": cap, "value": val, "meta": type, "desc": desc}


def gen_list(schema, prefix, ops):
    for k, v in schema.items():
        if isinstance(v, dict):
            if "valType" in v:
                ops.append(
                    gen_comp(f"{prefix}{k}", f"{prefix}{k}: {v.get('dflt', '')}", v["valType"], v.get("description")))
            elif v.get("role", "") == "object":
                gen_list(v, f"{prefix}{k}.", ops)


def generate_options_list(schema):
    cops = []
    lops = []
    trace_list = []  # List of available "trace" types (e.g., scatter, ....,...., etc.
    trace_opts = {}

    gen_list(schema["layout"]["layoutAttributes"], "layout.", lops)
    gen_list(schema["config"], "config.", cops)

    for k, v in schema["traces"].items():
        if isinstance(v, dict):
            trace_list.append(gen_comp(k, k, "plot type <string>", v.get("meta", {}).get("description", "")))

            trace_o = []
            gen_list(v.get("attributes", {}), "", trace_o)
            gen_list(v.get("layoutAttributes", {}), "", trace_o)
            trace_opts[k] = trace_o

    return {"config": cops, "layout": lops, "traces": trace_opts, "traceList": trace_list,
            "default": [
                gen_comp("layout", "layout", "Layout Options", ""),
                gen_comp("config", "config", "Config Options", ""),
                gen_comp("trace", "trace.unnamed: scatter", "Plot Type <str>", "Define a new Plot")
            ]}


def get_plotly_options_for(directive, option, value, pre, data) :
    if option.startswith("trace."):
        return plotly_options["traceList"]

    a = value.rfind("{{")
    if a > 0 and a > value.rfind("}}"):
        jmesp = value[a+2:]
        return jmespath_autocomplete(jmesp, data, value, pre)


    return []

try:
    plotly_schema
except:
    with open(os.path.join(os.path.dirname(__file__), "plot-schema.json")) as f:
        plotly_schema = json.load(f)["schema"]

    plotly_options = generate_options_list(plotly_schema)


def remove_prefix(li, pre, pref, trace=None):
    # Pre is the full prefix for the option
    # pref is the bit after the last dot.

    # ppref is the prefix before the pref.
    ppref = pre[0:-len(pref)]

    def adder(k):
        if trace is not None:
            return f"{trace}.{k['caption']}".startswith(pre)
        return k["caption"].startswith(pre)

    return [gen_comp(k["caption"][len(ppref):], k["value"][len(ppref):], k["meta"], k["desc"]) for k in li if adder(k)]


def plotly_options_list(pre, pref, all_opts):
    layout = "layout"
    if pre.startswith("layout") or pre in [layout[0:i] for i in range(1, len(layout))]:
        return remove_prefix(plotly_options["layout"], pre, pref)

    config = "config"
    if pre.startswith("config") or pre in [config[0:i] for i in range(1, len(config))]:
        return remove_prefix(plotly_options["config"], pre, pref)

    trace = pre.split(".")

    if len(pre) and len(trace) == 1:
        ret = []
        for k, v in all_opts.items():
            if k.startswith("trace"):
                ret.append(gen_comp(k[6:], k[6:] + ".", "Named Trace", ""))
        return ret

    elif len(trace) > 0:
        tr = trace[0]
        if f"trace.{tr}" in all_opts:
            return remove_prefix(plotly_options["traces"].get(all_opts[f"trace.{tr}"].lstrip(), []), pre, pref,
                                 trace=tr)

    ret = []
    for k, v in all_opts.items():
        if k.startswith("trace"):
            ret.append(gen_comp(k[6:], k[6:] + ".", "Named Trace", ""))

    return remove_prefix(ret + plotly_options["default"], pre, pref)


def plotly_array(ff, arrayOk=False):
    def f(t):
        if arrayOk:
            try:
                a = json.loads(t)
                if isinstance(a, list):
                    return [ff(aa) for aa in a]
                else:
                    raise ExtensionError("Invalid option not an array")
            except:
                pass
        return ff(t)

    return f


def plotly_info_array(arrayOk=False, **kwargs):
    def t(v):
        return json.loads(v)

    return t


def plotly_enumerated(values, arrayOk=False, **kwargs):
    def enumerate(t):
        for i in values:
            if isinstance(i, str):
                if t == i:
                    return i
            elif isinstance(i, bool):
                try:
                    a = plotly_boolean(False)(t)
                    if i == a:
                        return i
                except:
                    pass
            elif isinstance(i, float):
                try:
                    a = float(t)
                    if a == i:
                        return i
                except:
                    pass
            elif isinstance(i, int):
                try:
                    a = int(t)
                    if a == i:
                        return i
                except:
                    pass
            else:
                pass
        print("UNRECONIZED ENUM -- RETURNING ANYWAY BUT.... TODO make this an error")
        return i

    return plotly_array(enumerate, arrayOk)


def plotly_boolean(arrayOk=False, **kwargs):
    def plotly_boolean_(t):
        if t in ["1", "t", "T", "true", "True"]:
            return True
        elif t in ["0", "f", "F", "false", "False"]:
            return False
        raise ExtensionError(t + " is not valid boolean")

    return plotly_array(plotly_boolean_, arrayOk)


def plotly_number_internal(cls, min=None, max=None, arrayOk=False):
    def plotly_number_(t):
        try:
            a = cls(t)
            if min is not None and a < min:
                raise ExtensionError(t + " must be >= " + min)
            if max is not None and a > max:
                raise ExtensionError(t + " must be <= " + max)
            return a
        except:
            raise ExtensionError(t + " is not a number")

    return plotly_array(plotly_number_, arrayOk)


def plotly_number(min=None, max=None, arrayOk=False, **kwargs):
    return plotly_number_internal(float, min, max, arrayOk)


def plotly_integer(min=None, max=None, arrayOk=False, **kwargs):
    return plotly_number_internal(int, min, max, arrayOk)


def plotly_string(noBlank=False, values=None, arrayOk=False, **kwargs):
    def s(t):
        if values is not None and t not in values:
            raise ExtensionError(t + " not in " + values)
        if noBlank and len(t) == 0:
            raise ExtensionError(t + " can not be empty ")
        return t

    return plotly_array(s, arrayOk)


def plotly_color(arrayOk=False, **kwargs):
    def s(t):
        return t  # todo

    return plotly_array(s, arrayOk)


def plotly_colorlist(**kwargs):
    return plotly_color(True)


def plotly_colorscale(**kwargs):
    v = ["Greys", "YlGnBu", "Greens", "YlOrRd", "Bluered", "RdBu", "Reds", "Blues", "Picnic", "Rainbow",
         "Portland", "Jet", "Hot", "Blackbody", "Earth", "Electric", "Viridis", "Cividis"]
    return plotly_enumerated(values=v, arrayOk=False)


def plotly_angle(**kwargs):
    return plotly_number(min=-180, max=180, arrayOk=False)


def plotly_data_array(**kwargs):
    def func(t):
        try:
            a = json.loads(t)
            if isinstance(a, list):
                for i in a:
                    if isinstance(i, list):
                        plotly_data_array()(json.dumps(i))
                    elif isinstance(i, dict):
                        raise ExtensionError("Not a data array")
                return a
        except:
            pass
        raise ExtensionError("Must be an array")

    return func


def plotly_convert(keys, value, trace, data, all_traces):
    rendered = render_template_string(value, data=data)

    if trace == "layout":
        s = {}
        s.update(plotly_schema["layout"]["layoutAttributes"])
        for key,value in all_traces.items():
            s.update(plotly_schema["traces"].get(value,{}).get("layoutAttributes",{}))

    elif trace == "config":
        s = plotly_schema["config"]
    else:
        s = plotly_schema["traces"][trace]["attributes"]

    for i in keys:
        if i[0:5] in ["xaxis", "yaxis"]:
            s = s[i[0:5]]

        else:
            s = s[i]

    m = f'plotly_{s["valType"]}'
    if m in globals():
        return globals()[m](**s)(rendered)
    return rendered


def plotly_post_process_raw(text, data, file, ext):
    # Extract all the trace definitions -- trace.x = scatter trace.y = line
    # Turn it into an object
    rdata = {}

    textj = json.loads(text) if isinstance(text, str) else text

    options = textj["options"]

    evalContent = textj["content"]
    try:
        extra_data = eval(evalContent, {"np": np, "math": math, "json": json, "numpy": np});
        if isinstance(extra_data, dict):
            options.update(extra_data)
    except:
        pass

    t = "trace."
    traces = {"layout": "layout",
              "config": "config"}
    errors = {}

    for k, v in options.items():
        if k[0:len(t)] == t:
            traces[k[len(t):]] = render_template_string(v, data=data, file=file)

    for k, v in options.items():
        a = k.split('.')
        if k in ext or a[0] == "trace":
            pass
        else:
            a = k.split('.')
            if len(a) <= 1:
                raise ExtensionError("invalid arguement " + k)

            elif a[0] not in traces:
                traces[a[0]] = options.get("defaultTrace", "scatter")

            dc = rdata
            for c in a[0:-1]:
                dc = dc.setdefault(c, {})
            try:
                dc[a[-1]] = plotly_convert(a[1:], v, traces[a[0]], data, traces)
            except Exception as e:
                errors[k] = {"value": v, "error": str(e)}

    # Raw data is in the correct format, but it is not
    rawdata = {
        "layout": {},
        "config": {"responsive": True},
        "data": [],
        "errors": errors
    }

    for k, v in rdata.items():
        if k == "layout":
            rawdata["layout"] = v
        elif k == "config":
            rawdata["config"] = v
        else:
            v.setdefault("type", traces.get(k, "scatter"))
            v.setdefault("name", k)
            rawdata["data"].append(v)
    return rawdata


def plotly_post_process(text, data, file):
    return json.dumps(plotly_post_process_raw(text, data, file, PlotlyDirec.external))


class PlotlyOptionsDict(MutableMapping):
    """A dictionary that calls a function when a requested key does not
    exist in the dictionary"""

    def __init__(self):
        self.store = {
            "height": str,
            "width": str,
            "defaultTrace": str
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


class PlotlyChartDirective(JsonChartDirective):
    script_template = '''
            {{% with current_id = data.getRandom() %}}
            
            <div id="{{{{current_id}}}}">  
                <div class="{id_}" style="width:100%; height:100%;"></div>
                <script>
                    ( () => {{
                        const parent = $('#{{{{current_id}}}}')
                        const obj = {config}
                        Plotly.newPlot(parent.find('.{id_}')[0],obj['data'],obj['layout']);
                        
                        var url = "/directives/updates/{uid}/{{{{data.getFile()}}}}/{{{{data.getAAId()}}}}"
                        update_now(url,  1000, function(config) {{
                            var xx = JSON.parse(config)
                            Plotly.update(parent.find('.{id_}')[0],xx['data'],xx['layout']);
                        }})
                    }})()
                </script>
           </div>
           {{%endwith%}}

            '''


class PlotlyDirec(PlotlyChartDirective):
    required_arguments = 0
    optional_arguments = 0
    file_argument_whitespace = False
    has_content = True
    option_spec = PlotlyOptionsDict()
    external = ["width", "height", "defaultTrace"]

    postprocess = plotly_post_process

    ## We tag all the ids with the dataId because we only really generate the html once per test. So, if
    ## you have a test multiple times, we need to have the dataId different so they dont interfere.
    script_template = '''
                                {{% with current_id = data.getRandom() %}}
                    <div id="{{{{current_id}}}}">  


                 <div class="MainDiv" style="width:100%; height:100%; min-height:450px"></div>
                 <script>
                   ( () => {{
                       const parent = $('#{{{{current_id}}}}')
                       url = "/directives/updates/{uid}/{{{{data.getFile()}}}}/{{{{data.getAAId()}}}}?context=plotly"
                       var load = [88,12]
                   
                       Plotly.newPlot(parent.find(".MainDiv")[0],[
                           {{values: load, 
                             text:'Loading', 
                             textposition:'inside', 
                             hole: 0.5, 
                             labels: ['Loaded','Remaining'],
                             type: 'pie'}}
                          ],
                          {{
                            
                            showlegend:false,
                            annotations: [
                               {{ 
                                  font: {{ size: 20 }},
                                  showarrow: false,
                                  text: `${{load[0]}}%`,
                                  x: 0.5,
                                  y: 0.5
                               }}
                            ] 
                           }},
                           {{ }}
                       );
                       
                       update_now(url, 1000, function(config) {{
                         var xx = JSON.parse(config)
                         Plotly.react(parent.find('.MainDiv')[0],xx);     
                         Plotly.relayout(parent.find('.MainDiv')[0],{{}});                
                       }})
                       
                 }})()
                 </script>
                 </div>          {{%endwith%}}

                 '''

    def register(self):
        return self.getContent()

    def getRawContent(self):
        a = {"options": self.options, "content": "\n".join(self.content)}
        return json.dumps(a)


def setup(sapp):
    sapp.add_directive("vnv-plotly-raw", PlotlyChartDirective)
    sapp.add_directive("vnv-plotly", PlotlyDirec)

register_context("plotly", plotly_post_process)
