
from ...jmes import jmes_jinja_percentage
from .apex import ApexChartDirective


class ApexGaugeDirective(ApexChartDirective):
    required_arguments = 0
    optional_arguments = 0
    file_argument_whitespace = True
    has_content = False
    option_spec = {
        'value': str,
        'title': str
    }

    def getRawContent(self):
        return f'''
         {{
          "series": [ {self.options.get("value",53)} ] ,
          "chart": {{
            "type": "radialBar",
            "width" : "100%",
            "height" : "100%"
          }},
          "plotOptions": {{
            "radialBar": {{
              "hollow": {{
                "size": "70%"
              }}
            }}
          }},
          "labels": ["{self.options.get("title","VnV Gauge Chart")}"]
        }}
        '''

def setup(sapp):
    sapp.add_directive("vnv-gauge", ApexGaugeDirective)
