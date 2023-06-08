import os
import re

from app.moose import pyhit as py


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
