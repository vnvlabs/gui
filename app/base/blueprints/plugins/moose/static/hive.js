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


function set_schema(uuid) {

    $.post(`${HIVE_SCHEMA_URL}?schema=${uuid}&val=${encodeURIComponent($('#moose-exe').val())}`, function(data, s, xhr){

        addToast("Setting Schema", "", 4000)
        $('#schema_error').html(data)
        if (data.length > 0 ) {
            $('#schema_icon').show()
        } else {
            $('#schema_icon').hide()
        }

        if (xhr.status == 200) {

            addToast("Schema Set", "", 4000)
        } else {
            addToast("Schema Failed: " + data, "", 4000)
        }
    });
}

function set_hive_input_file(fileId) {

    $.post(`${HIVE_INPUT_URL}?inputfile=${encodeURIComponent($('#moose-input-file').val())}`, function(data, s, xhr){

        addToast("Setting Input File", "", 4000)

        if (xhr.status == 200) {
            $("#inp").html(data)
            addToast("Input File Loaded", "", 4000)
        } else {
            addToast("Input File Load Failed: " + data, "", 4000)
        }
    });
}

function save_hive_file(uuid) {
    var editor = ace.edit("view_file");
    var code = editor.getValue();
    addToast("Saving File", "", 4000)
    $.post(`${HIVE_SAVE_URL}?schema=${uuid}&val=${encodeURIComponent(code)}`, function(data, s, xhr){
        if (xhr.status == 200) {
            addToast("Save Successful","", 4000)
        } else {
            addToast("Save Failed: " + data, "", 4000)
        }
     });
}

function regen_mesh(uuid) {
    var editor = ace.edit("view_file");
    var code = editor.getValue();
    addToast("Regenerating Mesh", "", 4000)
    $.post(`${HIVE_MESH_URL}?schema=${uuid}&val=${encodeURIComponent(code)}`, function(data, s, xhr){

        if (xhr.status == 200) {
            $('#mesh_frame').attr('src', data)
            addToast("Regen Success","", 4000)
        } else {
            addToast("Mesh Generation Failed: " + data, "", 4000)
        }
     });
}


function toggle_mesh(uuid) {
    var editor = ace.edit("view_file");
    var code = editor.getValue();
    $('#mesh_file').toggle()
}


function format_hive_file(uuid) {
    var editor = ace.edit("view_file");
    var code = editor.getValue();
    addToast("Formatting File", "", 4000)
    $.get(`${HIVE_FORMAT_URL}?schema=${uuid}&val=${encodeURIComponent(code)}`, function(data, s, xhr){
        if (xhr.status == 200) {
            addToast("File Formatting Successful", "", 4000)
            editor.setValue(data)
        } else {
            addToast("Something went wrong", "", 4000)
        }
     });
}

function setup_hive_ace_editor(uuid){

    var input_editor = ace.edit(view_file,
    {
        theme: "ace/theme/tomorrow_night_blue",
        mode: "ace/mode/moose",
        autoScrollEditorIntoView: true,
        minLines: 40,
        enableBasicAutocompletion: true,
        enableLiveAutocompletion: false
    });

    var inputWordCompleter = {
      getCompletions: function(editor, session, pos, prefix, callback) {
        $.get(`${HIVE_AUTOCOMPLETE_URL}?schema=${uuid}&row=${pos.row}&col=${pos.column}&pre=${prefix}&val=${encodeURIComponent(editor.getValue())}`, function(data) {
            callback(null, data );
        });
      },
      getDocTooltip: function(item) {
         if (item.desc.length > 0 ) {
            item.docHTML = item.desc
         }
      }
    }
    langTools.addCompleter(inputWordCompleter)

    input_editor.session.on('change', function(delta) {

        $.get(`${HIVE_VALIDATE_URL}?schema=${uuid}&val=${encodeURIComponent(input_editor.getValue())}`, function(data, s, xhr) {
                input_editor.session.setAnnotations(data)
        });
    });

    //validate
    $.get(`${HIVE_VALIDATE_URL}?schema=${uuid}&val=${encodeURIComponent(input_editor.getValue())}`, function(data, s, xhr) {
                input_editor.session.setAnnotations(data)
    });

    //gen the mesh
    regen_mesh(uuid)
}