#! ./virt/bin/python 
# -*- encoding: utf-8 -*-
import argparse
import subprocess
import sys,json
import threading
import requests
import websocket
from flask import Flask, Blueprint, render_template, current_app, request, make_response, jsonify, send_file, g, Response
from flask_sock import Sock
import socketio as sio
from flask_socketio import SocketIO
from werkzeug.utils import redirect


blueprint = Blueprint(
    'base',
    __name__,
    url_prefix='',
    template_folder='templates'
)


@blueprint.route('/', methods=["GET"])
def home():
    return proxy("")


@blueprint.route("/paraview/", methods=["POST"])
def paraview_o():
    return make_response(jsonify({"sessionURL": current_app.config["WSPATH"]}), 200)


def get_ports():
    container = current_app.config["CONTAINER_PORT"]
    theia = current_app.config["THEIA_PORT"]
    paraview = current_app.config["PARAVIEW_PORT"]
    return container, theia, paraview

@blueprint.before_request
def authorize():
    if len(current_app.config["AUTH_CODE"]) and request.cookies.get("vnv-gui-code") != current_app.config["AUTH_CODE"]:
        return make_response("",401)


@blueprint.route('/<path:path>', methods=["GET", "POST"])
def proxy(path):
    def ppath(port, path=""):
        return f'http://{current_app.config["HOST"]}:{port}{path}'

    container, theia, paraview = get_ports()

    if path == "theia":
        return redirect("/?theia")

    elif path == "theia" or (path == "" and "theia" in request.args):
        PROXIED_PATH = ppath(theia)

    elif path == "paraview" or (path == "" and "paraview" in request.args):
        return render_template("pvindex.html")

    elif path in current_app.config["THEIA_FORWARDS"]:
        PROXIED_PATH = ppath(theia, request.full_path)

    elif path in current_app.config["PARAVIEW_FORWARDS"]:
        PROXIED_PATH = ppath(paraview, request.full_path)

    else:
        PROXIED_PATH = ppath(container, request.full_path)

    if request.method == "GET":
        resp = requests.get(PROXIED_PATH)
        excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
        headers = [(name, value) for (name, value) in resp.raw.headers.items() if
                   name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)
        return response

    elif request.method == "POST":
        try:
            request.is_json
        except Exception as e:
            print("What")

        if not request.is_json:
            resp = requests.post(PROXIED_PATH, data=request.form)
        else:
            resp = requests.post(PROXIED_PATH, json=request.get_json())

        excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
        headers = [(name, value) for (name, value) in resp.raw.headers.items() if
                   name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)

        return response
    else:
        print("Unsupported Query sent to proxy")


def register(socketio, apps, config):
    apps.register_blueprint(blueprint)

    # Forward all the socket connections.
    class SocketContainer:
        def __init__(self, pty, theia=False):
            self.pty = pty
            self.sock = None
            self.sid = request.sid
            self.theia = theia

        def connect(self):
            if self.sock is None:
                container, theia, paraview = get_ports()

                # If theia then set the docker theia port instead.
                container = theia if self.theia else container

                if container is not None:
                    self.sock = sio.Client()

                    self.sock.connect(f"http://localhost:{container}" , namespaces=[f"/{self.pty}"])

                    @self.sock.on('*', namespace=f"/{self.pty}")
                    def catch_all(event, data):
                        try:
                            socketio.emit(event, data, namespace=f"/{self.pty}", to=self.sid)
                        except Exception as e:
                            print(e)

        def to_docker_container(self, event, data):
            self.connect()
            if self.sock is not None:
                count = 0
                while count < 5:
                    try:
                        self.sock.emit(event=event, data=data, namespace=f"/{self.pty}")
                        count = 100
                    except:
                        threading.Event().wait(1)
                        count += 1
            else:
                socketio.emit("Could not connect", namespace=f"/{self.pty}", to=self.sid)

    socks = {
        "pty": {},
        "pypty": {},
        "theia": {},
        "pv": {}
    }

    sock = Sock(apps)

    class WSockApp:
        def __init__(self, ip, ws):
            self.wsock = websocket.create_connection("ws://localhost:" + str(ip) + "/ws")
            self.killed = False
            self.ws = ws

        def kill(self):
            self.killed = True

        def running(self):
            return not self.killed

        def send(self, mess):
            self.wsock.send(mess)

        def run(self):
            while not self.killed:
                mess = self.wsock.recv()
                self.ws.send(mess)

        def serve(self):
            threading.Thread(target=self.run).start()

    @sock.route("/ws")
    def echo(ws):
        container, theia, paraview = get_ports()
        wsock = WSockApp(paraview, ws)
        wsock.serve()
        while wsock.running():
            try:
                greeting = ws.receive()
                wsock.send(greeting)
            except Exception as e:
                wsock.kill()

    def wrap(pty):

        @socketio.on(f"{pty}-input", namespace=f"/{pty}")
        def pty_input(data):
            socks[pty].to_docker_container(f"{pty}-input", data)

        @socketio.on("resize", namespace=f"/{pty}")
        def pyresize(data):
            socks[pty].to_docker_container(f"resize", data)

        @socketio.on("connect", namespace=f"/{pty}")
        def pyconnect():
            socks[pty] = SocketContainer(pty)

        @socketio.on("disconnect", namespace=f"/{pty}")
        def pydisconnect():
            try:
                socks.pop(pty)
            except:
                pass

    wrap("pty")
    wrap("pypty")

    @socketio.on("connect", namespace=f"/services")
    def theiaconnect(**kwargs):
        socks["theia"] = SocketContainer("services", True)

    @socketio.on('message', namespace="/services")
    def catch_message(data, **kwargs):
        socks["theia"].to_docker_container(f"message", data)

    @socketio.on('disconnect', namespace="/services")
    def abcatch_disconnect(**kwargs):
        socks.pop("theia")


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


def create_serve_app(config):

    from engineio.payload import Payload
    Payload.max_decode_packets = 500

    app = Flask(__name__, static_url_path='/flask_static', static_folder="static")
    app.config.from_object(config)
    socketio = SocketIO(app, cors_allowed_origins="*")
    register(socketio, app, config)
    return socketio, app


class Config:
    DEBUG=False
    port = 5000
    HOST = "0.0.0.0"
    WSPATH = f"ws://{HOST}:{port}/ws"
    HOSTCORS = f"http://localhost:{port}"

    THEIA_LIB_DIR="/theia/lib"
    PARAVIEW_LIB_DIR="/paraview/share/paraview-5.10/web/visualizer/www"
    THEIA_PORT = 5003
    PARAVIEW_PORT = 5005
    CONTAINER_PORT = 5000

if __name__ == "__main__":

    app_config = Config()

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, help="port to run on (default 5001)", default=5001)
    parser.add_argument("--host", help="host to run on (default localhost)", default="0.0.0.0")
    parser.add_argument("--theia",type=int, help="port running theia",default=3000)
    parser.add_argument("--paraview",type=int, help="port running paraview",default=9000)
    parser.add_argument("--vnv", type=int, help="port running vnv", default=5001)
    parser.add_argument("--code", type=str, help="authorization-code", default="")
    parser.add_argument("--ssl", type=bool, help="should we use ssl", default=False)
    parser.add_argument("--ssl_cert", type=str, help="file containing the ssl cert", default=None)
    parser.add_argument("--ssl_key", type=str, help="file containing the ssl cert key", default=None)

    args = parser.parse_args()
    Config.port = args.port
    Config.THEIA_PORT = args.theia
    Config.PARAVIEW_PORT = args.paraview
    Config.CONTAINER_PORT = args.vnv
    Config.AUTH_CODE = args.code

    forwards = []
    pvforwards = subprocess.run(["ls", app_config.PARAVIEW_LIB_DIR], stdout=subprocess.PIPE).stdout.decode(
        'ascii').split("\n")

    for line in pvforwards:
        kk = line.replace("\t", " ")
        forwards = forwards + line.split(" ")

    app_config.PARAVIEW_FORWARDS = [a.strip() for a in forwards if len(a) > 0 and a != "index.html"]

    forwards = []
    theiaforwards = subprocess.run(["ls", app_config.THEIA_LIB_DIR], stdout=subprocess.PIPE).stdout.decode(
        'ascii').split("\n")
    for line in theiaforwards:
        kk = line.replace("\t", " ")
        forwards = forwards + kk.split(" ")
    app_config.THEIA_FORWARDS = [a.strip() for a in forwards if len(a) > 0 and a != "index.html"]

    socketio, app = create_serve_app(app_config)
    opts = {
        "use_reloader" : False,
        "host" : app_config.HOST,
        "port" : app_config.port
    }
    if args.ssl:
        opts["ssl_context"] = (args.ssl_cert, args.ssl_key)

    socketio.run(app, **opts)
