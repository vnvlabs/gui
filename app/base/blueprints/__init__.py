from . import notifications, inputfiles, directives, tempfiles, help

all_blueprints ={}
all_blueprints["inputfiles"] = inputfiles

try:
    from . import files 
    if files.VnVFileActive:
        all_blueprints["files"] = files
except:
    pass    
all_blueprints["temp"] = tempfiles
all_blueprints["help"] = help
all_blueprints["notifications"] = notifications
all_blueprints["directives"] = directives
all_blueprints["inputfiles"] = inputfiles

