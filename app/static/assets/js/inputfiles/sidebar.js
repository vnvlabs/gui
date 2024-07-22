
function remove_inputfile(id_) {
  event.preventDefault()

  confirm_modal("Remove Input File", "Removing an input file will remove it from the view, but not the file system. Do you still want to remove this file? ", "Yes","No", (e,m) =>{

     if (e) {
        $( "#inputfile-" + id_).remove();
        $.post( "/inputfiles/delete/" + id_, function( data ) {
            m.modal('hide')
            update_inputtree_data(true)
        });
     }
  })

  }

function add_input_file(event) {
   $('#new_inputfile_modal').modal()
   event.stopPropagation()
   event.preventDefault();
}


function delete_all_inputfiles(event) {
  event.preventDefault()
  event.stopPropagation()

  confirm_modal("This will delete all files. This cannot be undone", "Are you sure?" , "Yes","No", (e,m)=>{

     if (e) {

        url = "/inputfiles/delete-all"
        $.post(url, function( data ) {
            window.location.href = "/"
        });
     }
  })

  }

function save_input_config(fileid, elm) {
    markAsLoading(true,"Updating Input File Configuration");
    $.post("/inputfiles/configure/" + fileid, elm.serialize(), function(data) {
        $('#config_content_config').html(data)

        $.get("/inputfiles/update_main_header/" + fileid, function(data) {
            $("#main_header").html(data["header"]);
            ace.edit("specFile").getSession().setValue(data["spec"]);
            $('#main_desc').html(data["desc"])
            markAsLoading(false,"Input File Updated Successfully")
        })

    })
}



function close_inputfile_connection(fileid) {
    $.post("/inputfiles/disconnect/" + fileid, function(data) {
        $('#config_content_config').html(data)
    })
}





function save_input_object(fileid ,elm, object, then ) {

    a = {"value" : ace.edit(elm).getValue()};

    $.ajax("/inputfiles/" + object + "/" + fileid,
      {
        data : JSON.stringify(a),
        contentType : 'application/json',
        type : 'POST',
        success: function(data, s, xhr) {
            if (then != null) {
                then(data,s,xhr)
            } else {

               if (xhr.status == 200) {
                 //addToast("Save Successfull", "", 5000)
               } else {
                 alert("Something went wrong - Please try again.")
               }
            }
        }
    });
}

function save_input_input(fileid) {
  save_input_object(fileid,"inputfile", "save_input")
}
function save_input_spec(fileid) {
  save_input_object(fileid,"specfile", "save_spec")
}


function show_input_modal(fileId, modalId) {
    $.get("/inputfiles/connected/" + fileId , function(data,s,xhr) {
        if (xhr.status == 200) {
            $(modalId).modal('show')
        } else {
            alert("You must open a valid connection before loading an input file. ")
        }
    })
}


function get_ace_editor(fileid, elmId, mode, live, autocompl, autosave) {

    var input_editor = ace.edit(elmId,
    {
        theme: "ace/theme/tomorrow_night_blue",
        mode: "ace/mode/" + mode,
        autoScrollEditorIntoView: true,
        minLines: 40
    });

    if (autosave) {
        input_editor.session.on('change', function(delta) { autosave(delta); });
    }

    if (autocompl) {

        input_editor.setOptions({
            enableBasicAutocompletion: true,
            enableLiveAutocompletion: live
        });

        var inputWordCompleter = {
            getCompletions: function(editor, session, pos, prefix, callback) {
               if (ace.edit(elmId) == editor ) {
                 autocompl(editor,session,pos,prefix,callback);
               }
            },
            getDocTooltip: function(item) {
                if (item.desc.length > 0 ) {
                    item.docHTML = item.desc
                }
            }
        }
        langTools.addCompleter(inputWordCompleter)
    }

    const originalSetAnnotations = input_editor.session.setAnnotations

    input_editor.session.setAnnotations = function (annotations) {
      // If we have annotations already, then set them.
      if (annotations && annotations.length) {
        originalSetAnnotations.call(input_editor.session, annotations)
      } else {
        // Validate the thing and see if that works.
        $.ajax("/inputfiles/validate/" + elmId + "/" + fileid, {
          data : JSON.stringify({"value" : input_editor.getValue() }),
          contentType : 'application/json',
          type : 'POST',
          success: function(data, s, xhr) {
               originalSetAnnotations.call(input_editor.session, data)
          }
        });
      }
    }

    return input_editor
}

function refresh_jobs_list(fileId) {
        $.get("/inputfiles/joblist/" + fileId, function(data) {
            $('#input-file-job-list-' + fileId).html(data)
        })
}

function delete_exe_job(e,fileId, jobId) {
    e.stopPropagation();
    $.post("/inputfiles/delete_job/" + fileId + "/" + jobId, function(data) {
            $('#input-file-job-list-' + fileId).html(data)
    })

}

function cancel_exe_job(e, fileId, jobId) {
    e.stopPropagation();
    $.post("/inputfiles/cancel_job/" + fileId + "/" + jobId, function(data) {
            $('#input-file-job-list-' + fileid).html(data)
    })

}


function resetIFState() {
   $('.if-element-page').remove()
}

currentSelectedFile = null
currentSelectedElement = null

function updateIFState(ipid, fileId) {

   if (!fileId) {
        fileId = 0
   }
    debugger;
   currentSelectedFile = fileId
   currentSelectedElement = ipid

   eid = "if-element-" + ipid + fileId;
   elmid = "#" + eid
   $('.if-element-page').toggle(false)

   // If we have it already then show it.
   if ( $(elmid).length == 1 ) {
      $(elmid).toggle(true)
   } else {

      // Append to it a new element.
      $('#if-element').append("<div id='" + eid + "' class='if-element-page'> Loading .... </div>")
      var url = '/inputfiles/render/' + fileId + "?ipid=" + ipid;

      // Populate the element with the data
      $.get(  url , function( data ) {
         $(elmid).html(data)
      });
   }

}
