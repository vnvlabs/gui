
function upload_file_b(vnvfileid, filename, type, options) {

      url = "/browser/reader/upload/" + vnvfileid
      url += "?filename=" + filename
      url += "&modal=" + type

       $.post(url, function(data) {
          if (type.length == 0 ) {
            $('#file_viewer_modal_body').html(data)
            $('#file_viewer_modal').modal('show')
          } else {
            $('#' + type).html(data)
          }
       });

}

function show_file_reader(vnvfileid, filename, reader , type, options) {

       if (type.length == 0 ) {
         $('#file_viewer_modal').modal('show')
         if (options && !("noload" in options)) {
           $('#file_viewer_modal_body').html("<div>Loading...</div>")
         }
         $('#file_view_modal_dialog').css("max-width","90%")
       } else if (options && !("noload" in options)) {
         $('#' + type ).html("<div>Loading...</div>")
       }

       url = "/browser/reader/" + vnvfileid
       url += "?filename=" + filename
       url += "&modal=" + type
       if (reader.length > 0 ) {
            url += "&reader=" + reader
       }
       if (options) {
           for (i in options) {
             url += "&render_" + i + "=" + options[i]
           }
       }

       if (reader == "actual_upload") {
           var formData = new FormData();
           formData.append("filename",$('#uploadfilename').val());
           formData.append("file", $('#uploadfile').prop('files')[0])

           $.ajax({
              type : "POST",
              processData: false,
              contentType: false,
              url : url,
              data : formData,
              success : function(data) {
                if (type.length == 0 ) {
                  $('#file_viewer_modal_body').html(data)
                  $('#file_viewer_modal').modal('show')
                 }  else {
                   $('#' + type).html(data)
                 }
              }
           })
       } else {

        $.get(url, function(data) {
          if (type.length == 0 ) {
            $('#file_viewer_modal_body').html(data)
            $('#file_viewer_modal').modal('show')
          } else {
            $('#' + type).html(data)
          }
        });
       }
}

function close_connection(fileid, formid,file,reader,modal) {
        $.get('/browser/close_connection/' + fileid, function(data){
            show_file_reader(fileid,file,reader,modal)
        })

}

function open_connection(fileid, formid, file, reader, modal) {
        $.post('/browser/open_connection/' + fileid, $('#'+formid).serialize(), function(data){
            show_file_reader(fileid,file,reader,modal)
        })
}
