# -*- encoding: utf-8 -*-
import os
import subprocess
import threading
import requests
import websocket
from flask import Flask, current_app, request, Response, make_response, render_template
from flask_socketio import SocketIO
import socketio as sio
from flask_sock import Sock
from engineio.payload import Payload

class Config:
    DEBUG = False
    port = 5001
    PARAVIEW_DIR = "/paraview"
    THEIA_DIR = "/theia"
    THEIA_PORT = "3000"
    PARAVIEW_PORT = "9000"
    GUI_PORT = "5002"
    GUI_DIR = "/vnv-gui"
    GUI_PYTHON = "virt/bin/python3"
    MONGO = True

app_config = Config()

if app_config.MONGO:
    subprocess.run(["service","mongodb","start"])
    threading.Event().wait(2)

theia_process = subprocess.Popen([
    "node", Config.THEIA_DIR + "/src-gen/backend/main.js","${SOURCE_DIR}",
    "--port", Config.THEIA_PORT,
    "--hostname","127.0.0.1"], cwd=Config.THEIA_DIR)

paraview_process = subprocess.Popen([
    Config.PARAVIEW_DIR + "/bin/pvpython",
    "-m", "paraview.apps.visualizer",
    "--host", "127.0.0.1",
    "--data", "/",
    "--port", Config.PARAVIEW_PORT,
    "--timeout", "600000"], cwd=Config.PARAVIEW_DIR)

gui_process = subprocess.Popen([
    Config.GUI_PYTHON, "./run.py",
    "--host", "127.0.0.1",
    "--port", Config.GUI_PORT,
    "--theia", "/?theia",
    "--paraview", "/?paraview"
],cwd=Config.GUI_DIR, env={**os.environ, **{"PYTHONPATH":os.environ["VNV_DIR"]}})

forwards = []
pvforwards = subprocess.run(["ls", Config.PARAVIEW_DIR + "/share/paraview-5.10/web/visualizer/www"], capture_output=True)
pvf = pvforwards.stdout.decode('ascii')
for line in pvf.split("\n"):
    kk = line.replace("\t", " ")
    forwards = forwards + line.split(" ")
app_config.PARAVIEW_FORWARDS = [a.strip() for a in forwards if len(a) > 0 and a != "index.html"]

forwards = []
theiaf = subprocess.run(["ls", Config.THEIA_DIR + "/lib"], capture_output=True)
theiaff = theiaf.stdout.decode('ascii')
for line in theiaff.split("\n"):
    kk = line.replace("\t", " ")
    forwards = forwards + kk.split(" ")
app_config.THEIA_FORWARDS = [a.strip() for a in forwards if len(a) > 0 and a != "index.html"]

Payload.max_decode_packets = 500

app = Flask(__name__, static_url_path="/flask_static")
app.config.from_object(app_config)
socketio = SocketIO(app)

@app.route("/")
def home():
    return proxy("")

@app.route('/<path:path>', methods=["GET", "POST"])
def proxy(path):
    try:
        if path == "theia" or (path == "" and "theia" in request.args):
            PROXIED_PATH = "http://localhost:" + Config.THEIA_PORT
        elif path == "paraview" or (path == "" and "paraview" in request.args):
            PROXIED_PATH = "http://localhost:" + Config.PARAVIEW_PORT
        elif path in current_app.config["THEIA_FORWARDS"]:
            PROXIED_PATH = "http://localhost:" + Config.THEIA_PORT + request.full_path
        elif path in current_app.config["PARAVIEW_FORWARDS"]:
            PROXIED_PATH = "http://localhost:" + Config.PARAVIEW_PORT + request.full_path
        else:
            PROXIED_PATH = "http://localhost:" + Config.GUI_PORT + request.full_path

        if request.method == "GET":
            resp = requests.get(PROXIED_PATH)
            excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
            headers = [(name, value) for (name, value) in resp.raw.headers.items() if
                       name.lower() not in excluded_headers]
            response = Response(resp.content, resp.status_code, headers)
            return response

        elif request.method == "POST":
            if request.get_json() is None:
                resp = requests.post(PROXIED_PATH, data=request.form)
            else:
                resp = requests.post(PROXIED_PATH, json=request.get_json())

            excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
            headers = [(name, value) for (name, value) in resp.raw.headers.items() if
                       name.lower() not in excluded_headers]
            response = Response(resp.content, resp.status_code, headers)

            return response

    except Exception as e:
        return make_response(str(e), 200)

    return make_response("error", 200)


class SocketContainer:
    def __init__(self, pty, theia=False):
        self.pty = pty
        self.sock = None
        self.sid = request.sid
        self.theia = theia

    def connect(self):
        if self.sock is None:
            container = app.config["GUI_PORT"]
            theia = app.config["THEIA_PORT"]

            # If theia then set the docker theia port instead.
            container = theia if self.theia else container

            if container is not None:
                self.sock = sio.Client()
                self.sock.connect("http://localhost:" + container, namespaces=[f"/{self.pty}"])

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


socks = {}
sock = Sock(app)


class WSockApp:
    def __init__(self, ws):
        self.wsock = websocket.create_connection("ws://localhost:" + app.config["PARAVIEW_PORT"] + "/ws")
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
    wsock = WSockApp(ws)
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
        try:
            socks[pty] = SocketContainer(pty)
        except Exception as e:
            print(e)

    @socketio.on("disconnect", namespace=f"/{pty}")
    def pydisconnect():
        socks.pop(pty)


wrap("pty")
wrap("pypty")


@socketio.on("connect", namespace=f"/services")
def theiaconnect(**kwargs):
    socks["theia"] = SocketContainer("services", True)


@socketio.on('message', namespace="/services")
def catch_message(data, **kwargs):
    if "theia" in socks:
        socks["theia"].to_docker_container(f"message", data)


@socketio.on('disconnect', namespace="/services")
def abcatch_disconnect(**kwargs):
    if "theia" in socks:
        socks.pop("theia")


if __name__ == "__main__":
    socketio.run(app, use_reloader=False, host="0.0.0.0", port=app_config.port)
