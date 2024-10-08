
function loading() {

}

function delete_all_files(event) {
  event.preventDefault()

  confirm_modal("This will delete all files. This cannot be undone (files can be reloaded if you still have the raw vnv output)", "Are you sure?" , "Yes","No", (e,m)=>{

     if (e) {

        url = "/files/delete-all"
        $.post(url, function( data ) {
            window.location.href = "/"
        });
     }
  })

  }

function render_in_main_view(url) {
   $.get(url, function(data) {
        $('#formControlElm').html(data)
   })
}


function remove_file(id_) {

  confirm_modal( "Delete File", "Are you sure you want to remove the file from the interface? Note: This will not remove the file from the filesystem." , "Yes","No", (e,m)=>{

     if (e) {

        url = "/files/delete/" + id_
        $.post(url, function( data ) {
            m.modal('hide')
            update_tree_data(true)
        });
     } else {
         m.modal('hide')
     }
  })

  }

function add_file(event) {
   $('#new_file_modal').modal()
   event.stopPropagation()
   event.preventDefault();
}


function show_ip_rst_editor(fileId, testId, atestId ) {
     $.get('/files/viewers/rst/raw/' + fileId + '/' + testId, function(data) {
           set_rst(fileId, testId, atestId, data["rst"],data["dataviewer"]) ;
           $('#raw-modal').modal('toggle')
     });
}

function show_workflow_rst_editor(fileId, dataId,  creator, job ) {
     u = '/files/workflow/raw_rst/' + fileId + "?creator=" + encodeURIComponent(creator)
     if (job) {
        u += "&jobName=" + encodeURIComponent(job)
     }

     $.get(u, function(data) {
           set_rst(fileId, dataId, dataId, data["rst"],data["dataviewer"]) ;

           $('#raw-modal').modal('toggle')
     });
}

function show_data_explorer(fileId, testId) {
     $.get('/files/viewers/dataexplorer/' + fileId + '/' + testId, function(data) {
           $('#data-modal-body').html(data)
           $('#data-modal').modal('toggle')
     });
}



function start_processing_update(fileId, procTag) {
  $(window).on('load', function() {
        update_processing(fileId, procTag);
  });
}

function update_roles() {

   data = []
   elms = []
   $('[data-o="on"]').each(

     function(i){
        q = $(this).data('q')
        f = $(this).data('f')
        i = $(this).data('i')
        m = $(this).data('m')
        data.push([f,i,q,m])
        elms.push(this)
     }
   )
   if (data.length) {

     $.ajax({
        url: "/directives/roles" ,
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify(data),
        success: function(response){
            for (i=0; i < response.length; i++) {
                if ( $(elms[i]).data('t') == "span" ) {
                    $(elms[i]).text(response[i][1])
                } else {
                    $(elms[i]).html(response[i][1])
                }
                if (!response[i][0]) {
                    $(elms[i]).attr('data-o','off');
                }
            }
            setTimeout(update_roles, 3000)
        }
     });


   } else {
      setTimeout(update_roles, 3000)
   }


}

$(window).on('load', function() {
    update_roles()
    setInterval(function() {
       MathJax.typeset();
    }, 3000)
})

function update_processing(fileId, procTag) {
   $.get('/files/processing/' + fileId, function(data, textStatus, xhr) {

        if (xhr.status == 201) {
            $(procTag).hide();
        } else {
            setTimeout(function(){ update_processing(fileId, procTag) }, 3000);
        }
   });
}

function switch_package(fileId, name, element) {
    $(".prov-selected").removeClass("prov-selected");
    $('#'+name).addClass("prov-selected")

    $.get("/files/viewers/package/"+fileId + "?p=" + name, function(data) {
      $(element).html(data)
    })

}

function switch_action(fileId, name, element) {
  $(".action-selected").removeClass("action-selected");
  $(document.getElementById(name)).addClass("action-selected")

  $.get("/files/viewers/action/"+fileId + "?p=" + name, function(data) {
    $(element).html(data)
  })

}


function switch_pending(fileId, name, element) {
    $(".steering-selected").removeClass("steering-selected");
    $('#'+name).addClass("steering-selected")
    $.get("/steering/pending/"+fileId + "?p=" + name, function(data) {
      $(element).html(data)
    })
}

function switch_unit(fileId, name, id, element) {
    $(".unit-selected").removeClass("unit-selected");
    $('#'+name).addClass("unit-selected")

    $.get("/files/viewers/unit/"+fileId + "?uid=" + id, function(data) {
      $(element).html(data)
    })

}

function logout() {
    window.location.href = "/logout"
}

function scroll_line_into_view(line) {
    $(".linenodiv:visible")[0].children[0].children[line].scrollIntoView({behavior: "smooth", block: "center", inline: "nearest"})
}
function scroll_to_bottom() {
    a = $(".linenodiv:visible")[0].children[0]
    a.children[ a.children.length -1 ].scrollIntoView({behavior: "smooth", block: "center", inline: "nearest"})
}

const characters ='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';

function generateString(length) {
    let result = ' ';
    const charactersLength = characters.length;
    for ( let i = 0; i < length; i++ ) {
        result += characters.charAt(Math.floor(Math.random() * charactersLength));
    }

    return result;
}

function update_chart(url, timeout, chartupdate, response) {
        x = JSON.parse(response)
    
        chartupdate(x.config)

        if (x.more ) {
            update_soon(url,  timeout, chartupdate)
        }
}

function update_soon(url,  timeout, chartupdate) {
    
    setTimeout(function() {
        $.get(url, function(response) {
            update_chart(url,timeout,chartupdate,response)
        })
    }, timeout)
    
}

function update_now(url, timeout, chartupdate) {
        $.get(url, function(response) {
            update_chart(url, timeout,chartupdate,response);
        })
    
}

function getRandomString() {
    var S4 = function() {
       return (((1+Math.random())*0x10000)|0).toString(16).substring(1);
    };
    return (S4()+S4()+"-"+S4()+"-"+S4()+"-"+S4()+"-"+S4()+S4()+S4());
}

function update_request(fileId, ipid, elmid) {

   if ( $('#' + elmid ).length ) {
      url ="/files/viewers/iprequest/" + fileId + "/" + ipid
      $.get(url, function(data,status, xhr) {
        if (xhr.status == 200) {
           $('#' + elmid ).html(data)
        } else if (xhr.status == 201 ) {
           $('#' + elmid ).html("")
           setTimeout(function() {
              update_request(fileId, ipid, elmid)
           }, 3000)
        }
      })
    }

}

function  update_ip_processing(elm, file, ipid ) {
    if ( $('#' + elm ).length ) {
        url = "/files/viewers/processing/" + file + "/" + ipid
        $.get(url, function(response, status,  xhr) {
            $('#' + elm ).text(response)
            if (xhr.status == 200) {
                setTimeout(function() {
                   update_ip_processing(elm,file,ipid)
                },3000)
            }
        });
    }
}


function submit_form(elm, url, response) {
    $.ajax({
            url: url,
            type: 'post',
            data:$('#' + elm).serialize(),
            success: response
    });
}

function submit_response_form(containerId, ipFile, ipId ) {
    submit_form('steering_response_form', '/files/viewers/respond', function(data,stat,xhr) {
        $('#' + containerId).html("<div class='card' style='position:relative'><div class='card-body'><h3>Response Sent</h3></div></div>    ")
        setTimeout(function() {
          update_request(ipFile,ipId,containerId)
        }, 3000);
    });
}

function configure_response_validation(inputElmId, fid, ipid, action) {
  $('#' + inputElmId).bind('input propertychange', function() {
    $.ajax({
        url: '/files/viewers/validateResponse/' + fid + '/' + ipid ,
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({"data" : this.value }),
        success: function(response, stat, xhr){
           action(xhr.status == 200, response)
        }
     });
  })
}

$(window).on('load', function() {
    setInterval(function() {
       $('[data-countdown="on"').each(function () {
          $(this).text(parseInt($(this).text())-1)
       })
    }, 1000)
});


IPSTATE_CACHE = {}
current_ip_display = []

function resetIpState() {
   $('.injection-element-page').remove()
}

function updateIpState(ipid, fileId, processor, varies_with_proc) {

   if (!fileId) {
        fileId = 0
   }

   current_ip_display = [fileId, ipid, processor, varies_with_proc]

   eid = "injection-element-" + ipid;

   if (varies_with_proc) {
      eid += "-" + processor
   }

   elmid = "#" + eid
   $('.injection-element-page').toggle(false)

   // If we have it already then show it.
   if ( $(elmid).length == 1 ) {
      $(elmid).toggle(true)
   } else {



      // Append to it a new element.
      $('#injection-element').append("<div id='" + eid + "' class='injection-element-page'> Loading .... </div>")
      var url = '/files/viewers/ip/' + fileId + "?ipid=" + ipid + "&processor=" + processor;

      // Populate the element with the data
      $.get(  url , function( data ) {

         $(elmid).html(data)


      });
   }

}

$(document).ready(function() {
   $('a[data-toggle="pill"]').on('shown.bs.tab', function(e){
          var navElm = $(e.target)
          var target = navElm.attr("href") // activated tab
          var state = navElm.attr("state")
          var id = $(e.target).attr("id")

          if (state) {
            var x = localStorage.getItem("vnv_tab_state")
            var xx = {}
            if (x) {
                xx = JSON.parse(x)
            }
            xx[state] = id

            localStorage.setItem("vnv_tab_state", JSON.stringify(xx))
          }
    })

    x = localStorage.getItem("vnv_tab_state")
    if (x) {
        xx = JSON.parse(x)
        for (const [key, value] of Object.entries(JSON.parse(x))) {
            $('#' + value).tab("show")
        }
    }


});

