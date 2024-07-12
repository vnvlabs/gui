
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
       
        var pageUrl = '?filename=' + encodeURIComponent(filename);
        window.history.pushState('', '', pageUrl);

       if (type.length == 0 ) {
         $('#file_viewer_modal').modal('show')
         if (options && !("noload" in options)) {
           $('#file_viewer_modal_body').html("<div>Loading...</div>")
         }
         $('#file_view_modal_dialog').css("max-width","90%")
       } else if (!options || !("noload" in options)) {
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
              },

           })
       } else {

            $.ajax({
                url: url,
                type: "GET",
                success: function(data) {
                    if (type.length == 0 ) {
                        $('#file_viewer_modal_body').html(data)
                        $('#file_viewer_modal').modal('show')
                    } else {
                        $('#' + type).html(data)
                    }
                },
                error: function(xhr, status, error) {
                    if (type.length == 0 ) {
                        $('#file_viewer_modal_body').html("Could not open file or directory.")
                        $('#file_viewer_modal').modal('show')
                    } else {
                        $('#' + type).html("Could not open file or directory")
                    }
                },

            });

       }
}


/**
 * This is a small plugin demonstrating how to do custom languages.
 * You pretty much just define an Ace mode, make a FileKind for it,
 * and link your FileKind to it's appropriate extensions.
 */
(function() {

	// custom highlighting rules with GML-style tokens... and less code
	ace.define("ace/mode/moose_highlight_rules", [
		"require", "exports", "module",
		"ace/lib/oop", "ace/mode/text_highlight_rules", "ace/mode/folding/fold_mode"
	], function(require, exports, module) {
		"use strict";

		var oop = require("../lib/oop");
		var TextHighlightRules = require("./text_highlight_rules").TextHighlightRules;

		var tk_escape = "constant.language.escape";
		var rx_escape = "\\\\(?:[\\\\0abtrn;#=:]|x[a-fA-F\\d]{4})";
		var tk_key = "ini.variable";
		var tk_set = "ini.set.operator";
		var tk_val = "ini.string";
		var MooseHighlightRules = function() {

         this.$rules = {
                "start" : [

                     {
                         token : "comment",
                         regex : "#.*$"
                     },  {
                         token : "block",
                         regex : "\\[",
                         next : "mooseBlock"
                     }, {
                        token : "comment", // comments are not allowed, but who cares?
                        regex : "#.*$"
                    }, {
                        token : "keyword.operator.assignment.order",
                        regex : "\\border\\s*",
                        next : "orderequals"
                    }, {
                        token : "keyword.operator.assignment.family",
                        regex : "\\bfamily\\s*",
                        next : "familyequals"
                    } , {
                        token : "keyword.operator.assignment.elem_type",
                        regex : "\\belem_type\\s*",
                        next : "elem_typeequals"
                    }, {
                        token : "output_on",
                        regex : "\\boutput_on\\s*",
                        next : "output_on_block"
                    }, {
                        token : "execute_on",
                        regex : "\\bexecute_on\\s*",
                        next : "execute_on_block"
                    }, {
                        token : "keyword.control.moose",
                        regex : "\\btype\\s*",
                        next : "type_block"
                    }, {
                        token : "moose_equals",
                        regex : "[^=]"
                    }, {
                        token : "equals",
                        regex : "\\s*=\\s*",
                        next : "variable"
                    }
                ],

                "type_block" : [
                  {
                      token : "equals",
                      regex : "\\s*\\=\\s*",
                  }, {
                      token : "moose_type",
                      regex : "\\w*",
                      next : "start"
                 }
                ],

                "output_on_block" : [
                  {
                      token : "equals",
                      regex : "\\s*\\=\\s*",
                  },  {
                      token : "string_start",
                      regex : "\\s*\\'",
                      next : "output_on_check"
                  }, {
                      token : "invalid",
                      regex : "[^\\']",
                      next: "start"
                  }

                ],

                "output_on_check" : [
                    {
                      token : "constant.language.moose",
                      regex : "\\s*(none|initial|linear|nonlinear|timestep_end|timestep_begin|final|failed|custom)",
                    }, {
                        token : "string_end",
                        regex : "\\s*\\'",
                        next : "start"
                    }, {
                        token : "invalid",
                        regex : "[^\\']"
                    }

                ],

                "execute_on_block" : [
                  {
                      token : "equals",
                      regex : "\\s*\\=\\s*",
                  },  {
                      token : "string_start",
                      regex : "\\s*\\'",
                      next : "execute_on_check"
                  }, {
                      token : "invalid",
                      regex : "[^\\']",
                      next: "start"
                  }
                ],

                "execute_on_check" : [
                    {
                      token : "constant.language.moose",
                      regex : "\\s*(initial|linear|nonlinear|timestep_end|timestep_begin|final|custom)",
                    }, {
                        token : "string_end",
                        regex : "\\s*\\'",
                        next : "start"
                    }, {
                        token : "invalid",
                        regex : "[^\\']"
                    }

                ],

                "orderequals" : [
                  {
                      token : "equals",
                      regex : "\\s*=\\s*",
                  }, {
                      token : "constant.language.moose",
                      regex : "(CONSTANT|FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH)\\b",
                      next : "start"
                  }, {
                      token : "invalid",
                      regex : "\\w*",
                      next : "start"
                  }

                ],

                "familyequals" : [
                  {
                      token : "equals",
                      regex : "\\s*=\\s*",
                  }, {
                      token : "constant.language.moose",
                      regex : "(LAGRANGE|MONOMIAL|HERMITE|SCALAR|HIERARCHIC|CLOUGH|XYZ|SZABAB|BERNSTEIN|L2_LAGRANGE|L2_HIERARCHIC)\\b",
                      next : "start"
                  }, {
                      token : "invalid",
                      regex : "\\w*",
                      next : "start"
                  }

                ],
                 "elem_typeequals" : [
                  {
                      token : "equals",
                      regex : "\\s*=\\s*",
                  }, {
                      token : "constant.language.moose",
                      regex : "(EDGE|EDGE2|EDGE3|EDGE4|QUAD|QUAD4|QUAD8|QUAD9|TRI3|TRI6|HEX|HEX8|HEX20|HEX27|TET4|TET10|PRISM6|PRISM15|PRISM18)\\b",
                      next : "start"
                  }, {
                      token : "invalid",
                      regex : "\\w*",
                      next : "start"
                  }

                ],
                 "mooseBlock" : [
                    {
                        token : "keyword.control.moose",
                        regex : '(Adaptivity|Bounds|Mesh|MeshModifiers|Variables)',
                        next : "blockend"
                    },  {
                        token : "subsubdir",
                        regex : "\\.\\.\\/",
                        next : "supportfunction"
                    }, {
                        token : "subdir",
                        regex : "\\.\\/",
                        next : "subdir"
                    }, {
                        token : "blockend",
                        regex : "\\]",
                        next : "start"
                    }, {
                        token : "keyword.control.moose_invalid",
                        regex : "\\w+",
                        next : "blockend"
                    }
                ],

                "subdir" : [
                    {
                        token : "keyword.control.moose",
                        regex : "(TimeStepper|TimePeriods|Quadrature|Predictor|Adaptivity|Indicators|Markers|Periodic|InitialCondition|MortarInterfaces)",
                        next : "blockend"
                    }, {
                        token : "support.function.moose",
                        regex : "\\w+",
                        next: "blockend"
                    }
                ],

                "supportfunction" : [
                  {
                      token : "support.function.moose",
                      regex : "\\w+",
                      next : "blockend"
                  }, {
                        token : "blockEnd",
                        regex : "\\]",
                        next : "start"
                  }

                ],
                "blockend" : [
                    {
                        token : "blockEnd",
                        regex : "\\]",
                        next : "start"
                    }
                ] ,

                "variable" : [

                    {
                        token : "list", // single line
                        regex : '\'',
                        next  : "string"
                    }, {
                        token : "constant.numeric", // hex
                        regex : "0[xX][0-9a-fA-F]+\\b",
                        next : "start"
                    }, {
                        token : "constant.numeric", // float
                        regex : "[+-]?\\d+(?:(?:\\.\\d*)?(?:[eE][+-]?\\d+)?)?\\b",
                        next : "start"
                    }, {
                        token : "constant.language.boolean",
                        regex : "(?:true|false)\\b",
                        next : "start"
                    }, {
                        token : "constant.enum",
                        regex : "\\b\\w*\\b",
                        next : "start"
                    }
                ],
                "string" : [
                    {
                        token : "constant.language.escape",
                        regex : /\\(?:x[0-9a-fA-F]{2}|u[0-9a-fA-F]{4}|["\\/bfnrt])/,
                        next: "variable"
                    }, {
                        token : "list",
                        regex : '"|$',
                        next  : "variable"
                    }, {
                        defaultToken : "list"
                    }
                ],
            };

        };
		oop.inherits(MooseHighlightRules, TextHighlightRules);
		exports.MooseHighlightRules = MooseHighlightRules;
	});
	// mostly normal Ace
	ace.define("ace/mode/moose", ["require","exports","module",
		"ace/lib/oop","ace/mode/text","ace/mode/moose_highlight_rules"
	], function(require, exports, module) {

		var oop = require("../lib/oop");
		var TextMode = require("./text").Mode;
		var MooseHighlightRules = require("./moose_highlight_rules").MooseHighlightRules;

		var Mode = function() {
			this.HighlightRules = MooseHighlightRules;
			this.$behaviour = this.$defaultBehaviour;
		};
		oop.inherits(Mode, TextMode);

		(function() {
			this.lineCommentStart = ";";
			this.blockComment = null;
			this.$id = "ace/mode/moose";
		}).call(Mode.prototype);

		exports.Mode = Mode;
	});
})();
