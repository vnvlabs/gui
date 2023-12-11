import os
import re
import subprocess
import json
import pyhit 

def find_moose_executable(loc, **kwargs):
    """

    Args:
        loc[str]: The directory containing the MOOSE executable.

    Kwargs:
        methods[list]: (Default: ['opt', 'oprof', 'dbg', 'devel']) The list of build types to consider.
        name[str]: The name of the executable to locate, if not provided it will infer it from
                   a Makefile or the supplied directory
        show_error[bool]: (Default: True) Display error messages.
    """

    # Set the methods and name local variables
    if 'METHOD' in os.environ:
        methods = [os.environ['METHOD']]
    else:
        methods = ['opt', 'oprof', 'dbg', 'devel']
    methods = kwargs.pop('methods', methods)
    name = kwargs.pop('name', None)

    # If the 'name' is not provided first look for a Makefile with 'APPLICATION_NAME...' if
    # that is not found use the name of the directory
    if name is None:
        makefile = os.path.join(loc, 'Makefile')
        if os.path.isfile(makefile):
            with open(makefile, 'r') as fid:
                content = fid.read()
            matches = re.findall(r'APPLICATION_NAME\s*[:=]+\s*(?P<name>.+)$', content, flags=re.MULTILINE)
            name = matches[-1] if matches else None


    loc = os.path.abspath(loc)
    # If we still don't have a name, let's try the tail of the path
    if name is None:
        name = os.path.basename(loc)

    show_error = kwargs.pop('show_error', True)
    exe = None

    # Check that the location exists and that it is a directory
    if not os.path.isdir(loc):
        if show_error:
            print('ERROR: The supplied path must be a valid directory:', loc)

    # Search for executable with the given name
    else:
        # Handle 'tests'
        if name == 'test':
            name = 'moose_test'

        for method in methods:
            exe_name = os.path.join(loc, name + '-' + method)
            if os.path.isfile(exe_name):
                exe = exe_name
            break

    # Returns the executable or error code
    if (exe is None) and show_error:
        print('ERROR: Unable to locate a valid MOOSE executable in directory:', loc)
    return exe

def find_moose_executable_recursive(loc=os.getcwd(), **kwargs):
    """
    Locate a moose executable in the current directory or any parent directory.

    Inputs: see 'find_moose_executable'
    """
    loc = loc.split(os.path.sep)
    for i in range(len(loc), 0, -1):
        current = os.path.sep + os.path.join(*loc[0:i])
        executable = find_moose_executable(current, show_error=False)
        if executable is not None:
            break
    return executable


import re


insideBlockTag = re.compile(r'^\s*\[([^\]#\s]*)$')
parameterCompletion = re.compile(r'^\s*[^\s#=\]]*$')
otherParameter = re.compile(r"^\s*([^\s#=\]]+)\s*=\s*('\s*[^\s'#=\]]*(\s?)[^'#=\]]*|[^\s#=\]]*)$")
std_vector_pattern = re.compile(r'^std::([^:]+::)?vector<([a-zA-Z0-9_]+)(,\s?std::\1allocator<\2>\s?)?>$')
vec_pattern = re.compile(r'^std::vector<([^>]+)>$')

def object_assign(target, *sources):
    result = target.copy()
    for source in sources:
        result.update(source)
    return result


class Syntax:
    def __init__(self, tree):
        self.tree = tree

    def getSyntaxNode(self, path):
        if not len(path):
            return None

        b = self.tree["blocks"][path[0]]
        if b is None:
            return None

        ref = path[1:]
        for p in path[1:]:
            if "subblocks" in b and p in b["subblocks"]:
                b = b["subblocks"][p]
            elif "star" in b:
                b = b["star"]
            else:
                return None

        return b

    def getSubblocks(self, path):
        if not len(path):
            return list(self.tree["blocks"].keys())

        b = self.getSyntaxNode(path)
        if b is None:
            return []

        ret = []
        if "subblocks" in b:
            ret = b["subblocks"].keys()

        if "star" in b:
            ret.append("*")

        return sorted(ret)

    def getParameters(self, path, ptype):
        ret = {}
        object_assign(ret, self.tree["global"]["parameters"])

        b = self.getSyntaxNode(path)
        if b is None:
            return ret

        if "actions" in b:
            for k, v in b["actions"].items():
                object_assign(ret, v.get("parameters", {}))

        currentType = ptype
        if ptype is None:
            currentType = ret["type"]["default"] if "type" in ret else None

        if currentType:
            if (
                "subblock_types" in b
                and isinstance(b["subblock_types"], dict)
                and currentType in b["subblock_types"]
            ):
                object_assign(ret, b["subblock_types"][currentType]["parameters"])

            if (
                "types" in b
                and isinstance(b["types"], dict)
                and currentType in b["types"]
            ):
                object_assign(ret, b["types"][currentType]["parameters"])

        return ret

    def getTypes(self, path):
        ret = []

        b = self.getSyntaxNode(path)
        if b is not None:
            if "subblock_types" in b:
                for k, v in b["subblock_types"].items():
                    ret.append(
                        dict(
                            label=k,
                            documentation=v.get("description", k),
                            kind="parameter",
                        )
                    )

            if "types" in b:
                for k, v in b["types"].items():
                    ret.push(
                        dict(
                            label=k,
                            documentation=v.get("description", k),
                            kind="parameter",
                        )
                    )

        return ret


class Parser:
    
    def __init__(self):
        self.tree =None
    
    def parse(self, text):
        self.tree =  pyhit.load(text)        

    def get_block_list(self):
        return self.tree.get_block_list()
        
    def get_block_at_position(self, line, character):
        return self.tree.get_block_at_line(line)
        
    def get_block_parameters(self, node):
        return node.get_parameter()


def compute_filename_completion(regex, doc_vec, line, character):
    #TODO 
    return []



def isVectorOf(yamlType, type):
    match = std_vector_pattern.match(yamlType)
    return match and (match.group(2) == type)


def compute_value_completion(param , is_quoted, has_space, syntax, document_text_vec, line, character, parser): 
    
    
    single_ok =  not has_space
    vector_ok = is_quoted or  not has_space

    if (param["cpp_type"] == 'bool' and single_ok) or (isVectorOf(param["cpp_type"], 'bool') and vector_ok):
        return [
            {
                "label": 'true',
                "kind": "value"
            },
            {
                "label": 'false',
                "kind": "value"
            }
        ]


    if "options" in param:
        if (param["basic_type"] == 'String' and single_ok) or (param["basic_type"] == 'Array:String' and vector_ok):
            completions = []
            ref = param["options"].split(' ')
            for option in ref:
                item = {
                    "label": option,
                    "kind": "enumMember"
                }
                if ('option_docs' in param and option in param["option_docs"]):
                    item['documentation'] = param["option_docs"][option]
                
                completions.append(item)
            
            return completions

    # Perform the match
    match = vec_pattern.match(param["cpp_type"])
    if ((match and not vector_ok) or (not match and  not single_ok)):
        return []
    

    basic_type = match[1] if match else param["cpp_type"]
    if (basic_type == 'FileName') :
        return compute_filename_completion(re.compile(".*"), document_text_vec, line, character)
    
    if (basic_type == 'MeshFileName') :
        return compute_filename_completion(re.compile(".*\.(e|exd|dat|gmv|msh|inp|xda|xdr|vtk)$"), document_text_vec, line, character)
    
    if (basic_type == 'OutputName') :
        
        def f():
            ref1 = ['exodus', 'csv', 'console', 'gmv', 'gnuplot', 'nemesis', 'tecplot', 'vtk', 'xda', 'xdr']
            results = []
            for output in ref1:    
                results.append({
                    "label": output,
                    "kind": "folder"
                })
            
            return results 
            
        return f()
    

    if (basic_type in syntax.tree["global"]["associated_types"]):
        
        completions = []
        block_list = parser.get_block_list()
        
        matches_set = set(syntax.tree["global"]["associated_types"][basic_type])
        for match in matches_set:
            
            if (match[-2:] == '/*'):
                key = match[0:-1]
                for blockp in block_list:

                    block = blockp["path"].join('/')

                    if (block[0:len(key)] == key):
                        label = block[len(key):]
                        if (label.find('/') < 0):
                            completions.append({
                                "label": label,
                                "kind": "field"
                            })
                        
        return completions
    
    return []

def is_open_bracket_pair(line):
    return bool(insideBlockTag.search(line))


def is_parameter_complet(line):
    return parameterCompletion.search(line)



def paramDefault(param):
    if ("default" in param): 
        if (param["cpp_type"] == 'bool'):
            if (param["default"] == '0'):
                return 'false'
            
            if (param["default"] == '1'):
                return 'true'
            
        
        return param.default
    return None


def compute_completion(document_text, line, character, syntax, parser):
    
    document_text_vec = document_text.split()
    
    completions = []
    
    # current line up to the cursor position
    line = document_text_vec[line][0:character]
    
    # get the type pseudo path (for the yaml)
    cp = parser.get_block_at_position(line, character)
    
    if is_open_bracket_pair(line):
        # get a partial path
        line_match = re.match(insideBlockTag, line)
        if line_match:
            partial_path = line_match.group(1).replace(r'^\.\//', '').split('/')
            partial_path.pop()
        else:
            partial_path = []

        # get the postfix (to determine if we need to append a ] or not)
        post_line = document_text_vec[line][character:character+1]
        
        # add block close tag to suggestions
        block_postfix = "" if len(post_line) > 0 and post_line[0] == "]" else "]"
        if cp.path and partial_path:
            completions.append({"label": "..", "insertText": "[" + block_postfix})
        
        cp.path += partial_path
        subblocks = syntax.getSubblocks(cp.path)
        added_wildcard = False
        for completion in subblocks:
            # add to suggestions if it is a new suggestion
            if completion == "*":
                if not added_wildcard:
                    completions.append(
                        {
                            "label": "*",
                            "insertText": f"{name}" + block_postfix,
                            "insertTextFormat": "Snippet",
                        }
                    )
                    added_wildcard = True
                    
            elif completion != "":
                if not any(c["label"] == completion for c in completions):
                    completions.append({"label": completion, "insertText": completion + block_postfix})
        return completions

    # get parameters we already have and parameters that are valid
    existing_params = parser.get_block_parameters(cp.node)
    valid_params = syntax.get_parameters({"path": cp.path, "type": existing_params["type"]})

    # suggest parameters
    if is_parameter_complet(line):
        # loop over valid parameters
        for name, param in valid_params.items():
            # skip deprecated params
          

            # skip parameters that are already present in the block
            if name in existing_params:
                continue

            # format the default value
            default_value = paramDefault(param) or ""
            if " " in default_value:
                default_value = f"'{default_value}'"

            # set icon and build completion
            icon = (
                "parameter"
                if param["name"] == "type"
                else "constructor"
                if param["required"]
                else "variable"
                if param["default"] is not None
                else "field"
            )
            completions.append(
                {
                    "label": param["name"],
                    "insertText": f"{param['name']} = {default_value if default_value else ''}",
                    "insertTextFormat": "snippet" if default_value else None,
                    "documentation": param["description"],
                    "detail": f"(required) {paramDefault(param)}",
                    "kind": icon,
                    "tags": ["depreciated"] if param["deprecated"] else [],
                }
            )

        return completions

    # value completion
    match = otherParameter.search(line)
    if match:
        param_name = match.group(1)
        is_quoted = match.group(2)[0] == "'"
        has_space = bool(match.group(3))

        param = valid_params.get(param_name)
        if param is None:
            return []
        # this takes care of 'broken' type parameters like Executioner/Qudadrature/type
        if param_name == "type" and param["cpp_type"] == "std::string":
            completions = syntax.get_types(cp.path)
        elif param_name == "active" or param_name == "inactive":
            # filter direct subblocks from block list
            block_list = parser.get_block_list()
            path = "/".join(cp.path)
            for b in block_list:
                sub_path = "/".join(b["path"])
                if sub_path.startswith(path):
                    sub_path = sub_path[len(path) + 1:]
                    if "/" not in sub_path:
                        completions.append({"label": sub_path, "kind": "Array"})
            return completions
        else:
            completions = compute_value_completion(param, is_quoted, has_space, syntax, document_text_vec, line, character, parser)

    return completions



def get_suggestions(document_text, line, character, syntax) :
    parser = Parser()
    parser.parse(document_text)
    if parser.tree:
        return compute_completion(document_text, line, character, syntax, parser)

    # no completion available
    return []

def extract_moose_schema( filename, **kwargs):

        if filename is None:
            return {}, "No Schema Provided"
        
        elif not os.path.exists(filename):
            return {}, "Executable does not exist"

        try:
            args = kwargs.get("args",["--json"])
            cwd = kwargs.get("cwd", os.path.dirname(filename))
            a = subprocess.check_output([filename] + args, cwd=cwd, timeout=10).decode('ascii')
            akey = "**START JSON DATA**"
            ekey = "**END JSON DATA**"
            start_pos = a.find(akey) + len(akey)
            end_pos = a.find(ekey)
            return json.loads(a[start_pos:end_pos])
           
        except Exception as e:
            print(e)
            return {}, "Error: " + str(e)



if __name__ == "__main__":
    
    with open("ex01.i",'r') as f:
        val = f.read()
        schema = Syntax(extract_moose_schema("/vnvlabs/applications/moose/examples/ex01_inputfile/ex01-opt"))
        
        get_suggestions(val, 10, 30, schema)