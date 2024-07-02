try:
    from . import browser, notifications, files, inputfiles, directives, tempfiles, help, plugins
    HAS_VNV=True
except Exception as e:
    print(e)
    HAS_VNV=False
    