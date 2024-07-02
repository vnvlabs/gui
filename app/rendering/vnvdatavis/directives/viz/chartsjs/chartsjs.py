import json

from ..apex.apex import apex_post_process, ApexChartDirective, ApexOptionsDict
from ...jmes import register_context


def chartsjs_post_process(text, data, file):
    return apex_post_process(text,data,file,None)


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

script_template = '''
                      {{% with current_id = data.getRandom() %}}
                    <div id="{{{{current_id}}}}">  

       <div class="main-div" width="100%" height="100%">
          <canvas class='canvas-div'></canvas>
       </div>
       <script>           ( () => {{
         const obj = JSON.parse(`{config}`)
         
         const parent = $('#{{{{current_id}}}}')
         
         var ctx = parent.find('.canvas-div')[0] 
         
         var myChart = new Chart(ctx, obj);

         url = "/directives/updates/{uid}/{{{{data.getFile()}}}}/{{{{data.getAAId()}}}}"
         update_now(url, 1000, function(config) {{
            myChart.config = JSON.parse(config)
            myChart.update()  
         }})
       }})   }})()
       </script>
       </div>          {{%endwith%}}

       '''

class ChartsJsChartDirective(ApexChartDirective):

    script_template = '''
         {{% with current_id = data.getRandom() %}}
                    <div id="{{{{current_id}}}}">  

         <div>
           <div class='vnv-table'>
              <canvas class="canvas-div"></canvas>
           </div>
    
           <div class="apex-error-main main-errors" 
               style="color:orangered; font-size:30px; width:40px; height:40px; position:absolute; top:3px; right:3px; cursor:pointer; display:none">
               <i onclick="$(this).parent().parent().find('.main-error-message').toggle()" class="feather icon-alert-triangle" ></i>
           </div>
           <div class="card main-error-message" style="display:none; position:absolute; margin:20px; padding=20px; z-index:1000; top:43px; right:43px;"></div>   
         </div> 
         <script>
        
           ( () => {{
                 const parent = $('#{{{{current_id}}}}')
                 
                 var ctx = parent.find(".canvas-div")[0];
                 var myChart = new Chart(ctx, {loading});
    
                 url = "/directives/updates/{uid}/{{{{data.getFile()}}}}/{{{{data.getAAId()}}}}{context}"
                 update_now(url, 1000, function(config) {{
                     z = JSON.parse(config)
                     myChart.options = z.options
                     myChart.config = z 
                     myChart.update()
                     if (z["errors"]) {{
                        parent.find('.main-errors').show()   
                        parent.find('.main-error-message').html(z["errors"])
                      }} else {{
                        parent.find('.main-errors').hide()   
                    }}
                 }})
                 
             }})()
             
          </script>
          </div>
          {{%endwith%}}
        '''

    def getContext(self):
        return ""

    def getLoading(self):
        return loading

    def register(self):
        return self.getContent()


class ChartsJsDirec(ChartsJsChartDirective):
    required_arguments = 0
    optional_arguments = 0
    file_argument_whitespace = False
    has_content = False
    option_spec = ApexOptionsDict()

    def getContext(self):
        return "?context=jscharts"

    def register(self):
        return self.getContent()

    def getRawContent(self):
        return json.dumps(self.options)


def setup(sapp):
    sapp.add_directive("vnv-charts-js-raw", ChartsJsChartDirective)
    sapp.add_directive("vnv-charts-js", ChartsJsDirec)
    sapp.add_directive("vnv-chart", ChartsJsChartDirective)

register_context("jscharts", chartsjs_post_process)
