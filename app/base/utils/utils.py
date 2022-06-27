from flask import render_template


def render_error(code, message, nohome=False):
    return render_template(
        'page-custom.html', message=message, code=code, nohome=nohome), code
