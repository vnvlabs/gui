
import shutil

from flask import Flask,render_template
from logging import DEBUG

from flask_socketio import SocketIO
from flaskext.markdown import Markdown

global_template_variables = {

}


def register_blueprints(apps, config):

    import app.base

    base.config(config)
    apps.register_blueprint(base.blueprint)
    base.template_globals(global_template_variables)


    @apps.context_processor
    def inject_stage_and_region():
        return global_template_variables


def configure_error_handlers(app):
    @app.errorhandler(404)
    def fourohfour(e):
        return render_template('page-404.html'), 404

    @app.errorhandler(403)
    def fourohthree(e):
        return render_template('page-403.html'), 403

    @app.errorhandler(500)
    def fivehundred(e):
        return render_template('page-500.html'), 500


def create_app(config):
    app = Flask(__name__, static_folder='static')
    Markdown(app)

    app.config.from_object(config)
    register_blueprints(app, config)
    configure_error_handlers(app)
    return app

