
from ..charts import JsonChartDirective

try:
    the_app
except NameError:
    the_app = None

class TerminalDirective(JsonChartDirective):
    script_template = '''
                   {{% with current_id = data.getRandom() %}}
                    <div id="{{{{current_id}}}}">  

            <div class='card' style="height: 800px; overflow: auto; padding: 15px; background: #3c465b;"></div>
            <script>           ( () => {{
                 const parent = $('#{{{{current_id}}}}')
                 url = "/directives/updates/{uid}/{{{{data.getFile()}}}}/{{{{data.getAAId()}}}}"
                 update_now(url, 3000, function(config) {{
                      parent.find('.card').html("<pre class='term'>" + config + "</pre>")
                 }});    
                 }})()
            </script></div>          {{%endwith%}}
 '''

    def register(self):
        return self.getContent()

def setup(sapp):
    global the_app
    the_app = sapp

    sapp.add_directive("vnv-terminal", TerminalDirective)
