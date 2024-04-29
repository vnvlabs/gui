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
import signal
import os


class Config:
    DEBUG=False
    port = 5000
    HOST = "0.0.0.0"
    WSPATH = f"ws://{HOST}:{port}"

    PARAVIEW=True
    PARAVIEW_DIR="/vnvgui/paraview"
    PARAVIEW_PORT = 5005
    PARAVIEW_FORWARDS = []
    PARAVIEW_SESSION_PORT_START=6000
    PARAVIEW_DATA_DIR="/"

    THEIA = True
    THEIA_DIR="/vnvgui/theia"
    THEIA_PORT = 5003
    THEIA_FORWARDS = []
    
    VNV=True
    VNV_DIR="./"
    VNV_PORT = 5000


blueprint = Blueprint(
    'base',
    __name__,
    url_prefix='',
    template_folder='app/base/templates',
    static_folder="app/static"
)



@blueprint.route('/', methods=["GET"])
def home():
    return proxy("")


paraview_sessions = {
        "CURR_PORT" : Config.PARAVIEW_SESSION_PORT_START,
}

def start_paraview_server(filename):
    paraview_sessions["CURR_PORT"] += 1
    port = paraview_sessions["CURR_PORT"] - 1
   
    cmd =  [
        "bin/pvpython", "-m", "paraview.apps.visualizer", "--host", Config.HOST, "--port", str(port), "--data" , Config.PARAVIEW_DATA_DIR, "--timeout", str(600000)
    ]
   
    if filename is not None and os.path.exists(filename):
        f = os.path.abspath(filename)
        cmd += ["--load-file", f[1:] ]
    
    paraview_sessions[port] = subprocess.Popen(cmd, cwd=Config.PARAVIEW_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,preexec_fn=os.setsid)
    
    paraview_sessions[port].stdout
    while paraview_sessions[port].returncode is None:
        line = paraview_sessions[port].stdout.readline()
        print(line)
        if "Starting factory" in line.decode("ascii"):
            break  
        else:
            print("Nope")
    
    return port
   
@blueprint.route("/pv")
def vis_file():
    if Config.PARAVIEW == 0:
        return f"""<div> Error: Paraview Is Not Configured. Cannot open file.</div>"""
    
    src_url = f'/paraview?file={request.args.get("file","")}'
    iframe = f"""<iframe id='paraview' src="{src_url}" style="flex: 1; width:100%; height:100%; margin-bottom: 0px; border: none;"></iframe>"""
    return iframe,200

@blueprint.route("/paraview/", methods=["POST"])
def paraview_o():
    
    if Config.PARAVIEW == 0:
        return make_response(jsonify({"error": "paraview not configured"}), 200)
    
    uid = current_app.config["PARAVIEW_PORT"]
    if len(request.args.get("file",""))>0:
        
        filename = request.args["file"]
        if os.path.exists(filename):
            uid = start_paraview_server(filename)
        else:
            uid = start_paraview_server(None)
             
    return make_response(jsonify({"sessionURL": f"{current_app.config['WSPATH']}/ws/{uid}"}), 200)

def get_ports():
    container = current_app.config["VNV_PORT"]
    theia = current_app.config["THEIA_PORT"]
    paraview = current_app.config["PARAVIEW_PORT"]
    return container, theia, paraview

@blueprint.before_request
def authorize():

    AUTHCODE = current_app.config["AUTH_CODE"]
    if AUTHCODE is None or len(AUTHCODE) == 0:
        return

    if request.cookies.get("vnv-gui-code") == AUTHCODE:
        return None
    elif "code" in request.args and request.args.get("code") == AUTHCODE:
        r = make_response(redirect("/"), 302)
        r.set_cookie("vnv-gui-code", AUTHCODE)
        return r
    elif request.endpoint and 'static' in request.endpoint:
        return None
    elif request.endpoint == "base.login":
        return None

    return render_template('login.html', next=request.url)



@blueprint.route('/login', methods=["POST"])
def login():
    code = request.form.get("password")
    if code != current_app.config["AUTH_CODE"]:
        return render_template("login.html", error=True )
    
    r = make_response(redirect("/"), 302)
    r.set_cookie("vnv-gui-code", code)
    return r


@blueprint.route('/logout', methods=["POST"])
def logout():
    code = request.form.get("password")
    if code != current_app.config["AUTH_CODE"]:
        return render_template("login.html", error=True)

    r = make_response(redirect("/"), 302)
    r.set_cookie("vnv-gui-code", "__", expires=0)
    return r

@blueprint.route('/<path:path>', methods=["GET", "POST"])
def proxy(path):
    
    def ppath(port, path=""):
        return f'http://{current_app.config["HOST"]}:{port}{path}'

    container, theia, paraview = get_ports()

    if path == "theia":
        return redirect("/?theia")

    elif path == "" and "theia" in request.args:
        PROXIED_PATH = ppath(theia)

    elif path == "paraview" or (path == "" and "paraview" in request.args):
        if "file" in request.args:
            return render_template("pvindex1.html", sessionManagerURL="/paraview/?file=" + request.args.get("file"))
        return render_template("pvindex.html")

    elif path in current_app.config["THEIA_FORWARDS"]:
        PROXIED_PATH = ppath(theia, request.full_path)

    elif path in current_app.config["PARAVIEW_FORWARDS"]:
        PROXIED_PATH = ppath(paraview, request.full_path)

    else:
        PROXIED_PATH = ppath(container, request.full_path)

    if request.method == "GET":
        resp = requests.get(PROXIED_PATH, allow_redirects=False)
        
        if resp.status_code == 302:
            from urllib.parse import urlparse
            p = urlparse(resp.headers["Location"])
            return redirect(p.path),302
        
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
            resp = requests.post(PROXIED_PATH, data=request.form, allow_redirects=False)
        else:
            resp = requests.post(PROXIED_PATH, json=request.get_json(), allow_redirects=False)
        
        if resp.status_code == 302:
            from urllib.parse import urlparse
            p = urlparse(resp.headers["Location"])
            return redirect(p.path),302
         
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

    socks = {}

    sock = Sock(apps)

    class WSockApp:
        def __init__(self, ip, ws):
            self.wsock = websocket.create_connection(ip)
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

    def kill_and_kill_children(pid):
        os.killpg(os.getpgid(pid), signal.SIGKILL) 
        
        
    @sock.route("/ws/<uid>")
    def echo(ws, uid):
        wsock = WSockApp(f"ws://localhost:{uid}/ws", ws)
        wsock.serve()
        while wsock.running():
            try:
                greeting = ws.receive()
                wsock.send(greeting)
            except Exception as e:
                wsock.kill()
        
        wsock.kill()
        if int(uid) != current_app.config["PARAVIEW_PORT"]:
            proces = paraview_sessions.pop(int(uid))
            kill_and_kill_children(proces.pid)

    @socketio.on("connect", namespace=f"/services")
    def theiaconnect(**kwargs):
        socks[request.sid] = SocketContainer("services", True)

    @socketio.on('message', namespace="/services")
    def catch_message(data, **kwargs):
        socks[request.sid].to_docker_container(f"message", data)

    @socketio.on('disconnect', namespace="/services")
    def abcatch_disconnect(**kwargs):
        socks.pop(request.sid)


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

child_processes = []

def launch_theia(theia_directory, logs_directory, hostname, port):
       if os.path.exists(f"{theia_directory}/browser-app/src-gen/backend/main.js"):
            
            curr_dir = os.getcwd()
            os.chdir(theia_directory)
  
            command = [
                'node',
                './browser-app/src-gen/backend/main.js',
                '/',
                '--port', str(port),
                '--hostname=' + hostname,
                f'--plugins=local-dir:{Config.THEIA_DIR}/browser-app/plugins'
            ]
            
            log_file = f'{logs_directory}/theia_logs'
            with open(log_file, 'w') as log:
                child_processes.append(subprocess.Popen(command, stdout=log, stderr=log))

            os.chdir(curr_dir)
       else:
           Config.THEIA=0
           print("Could not start Theia")
 
def set_theia_forwards():
    forwards = []
    theiaforwards = subprocess.run(["ls", os.path.join(Config.THEIA_DIR,"browser-app/lib/frontend")], stdout=subprocess.PIPE).stdout.decode(
        'ascii').split("\n")
    for line in theiaforwards:
        kk = line.replace("\t", " ")
        forwards = forwards + kk.split(" ")
    Config.THEIA_FORWARDS = [a.strip() for a in forwards if len(a) > 0 and a != "index.html"] + ["os"]
   
   
   
def launch_paraview(paraview_directory, data_directory, logs_directory, hostname, port):
    if os.path.exists(f"{paraview_directory}/bin/pvpython"):
        
        curr_dir = os.getcwd()
        os.chdir(paraview_directory)
  
        command = [
            'bin/pvpython',
            '-m',
            'paraview.apps.visualizer',
            '--host', hostname,
            '--data', data_directory,
            '--port', str(port),
            '--timeout', "600000"
        ]
        
        log_file = f'{logs_directory}/paraview_logs'
        with open(log_file, 'w') as log:
            child_processes.append(subprocess.Popen(command, stdout=log, stderr=log))

        os.chdir(curr_dir)
    else:
        Config.PARAVIEW = 0
        print("Could not start Paraview")
 
def set_paraview_forwards():
     
     forwards = []
     pvforwards = subprocess.run(["ls", os.path.join(Config.PARAVIEW_DIR,"share/paraview-5.10/web/visualizer/www")], stdout=subprocess.PIPE).stdout.decode('ascii').split("\n")

     for line in pvforwards:
        kk = line.replace("\t", " ")
        forwards = forwards + kk.split(" ")

     Config.PARAVIEW_FORWARDS = [a.strip() for a in forwards if len(a) > 0 and a != "index.html"]
            

def launch_vnv_gui(vnv_directory, logs_directory, hostname, port):
    if os.path.exists(os.path.join(vnv_directory,"virt/bin/python")):
        currdir = os.getcwd()
        os.chdir(vnv_directory)

        command = [
            'virt/bin/python',
            './run.py',
            '--host', hostname,
            '--port', str(port),
            '--paraview', str(Config.PARAVIEW) ,
            '--theia', str(Config.THEIA)
        ]
        
        # Redirect stdout and stderr to the log file
        log_file = f'{logs_directory}/gui_logs'
        with open(log_file, 'w') as log:
            child_processes.append(subprocess.Popen(command, stdout=log, stderr=log))

        os.chdir(currdir)
    else:
        print("Could not start VnV")
        exit(0)

def signal_handler(sig, frame):
    print("Termination signal received. Terminating child processes...")
    # Terminate all child processes
    for process in child_processes + list(paraview_sessions.values()):
        try:
            process.terminate()
        except:
            pass
    
    print("Child processes terminated.")
    # Exit the parent process
    exit(0)

# Set up signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


    
if __name__ == "__main__":


    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, help="port to run on (default 5001)", default=5000)
    parser.add_argument("--host", help="host to run on (default localhost)", default="0.0.0.0")
    parser.add_argument("--wspath", type=str, help="ws path to use when connecting to paraview" )
    parser.add_argument("--code", type=str, help="authorization-code", default="")
    parser.add_argument("--ssl", type=bool, help="should we use ssl", default=False)
    parser.add_argument("--ssl_cert", type=str, help="file containing the ssl cert", default=None)
    parser.add_argument("--ssl_key", type=str, help="file containing the ssl cert key", default=None)
    parser.add_argument("--logs_dir", type=str, help="directory to write all the logs", default="/vnvgui/logs")
    
    parser.add_argument("--paraview",type=int, help="Run Paraview (0=off, 1=launch, 2=already running)",default=1)
    parser.add_argument("--paraview_port",type=int, help="port running paraview",default=9000)
    parser.add_argument("--paraview_port_start",type=int, help="port running paraview",default=9001)
    parser.add_argument("--paraview_dir", type=str, help="directory containing paraview install", default="/vnvgui/paraview")
    parser.add_argument("--paraview_data_dir", type=str, help="root directory for the visualizer", default="/")
    
    parser.add_argument("--theia",type=int, help="run theia (0=off, 1=launch, 2=already running)",default=1)
    parser.add_argument("--theia_port",type=int, help="port running theia",default=3000)
    parser.add_argument("--theia_dir", type=str, help="directory containing theia install", default="/vnvgui/theia")
    
    parser.add_argument("--vnv", type=int, help="Run the VnV Gui (0=off, 1=launch, 2=already running)", default=1)
    parser.add_argument("--vnv_port", type=int, help="Port to run vnvgui on ", default=5001)
    parser.add_argument("--vnv_dir", type=str, help="directory containing vnv gui", default="/vnvgui/gui")
    
    args, unknown = parser.parse_known_args()
    Config.port = args.port
    Config.HOST = args.host
    Config.AUTH_CODE = args.code
    
    if args.wspath:
        Config.WSPATH = args.wspath
    elif args.ssl:
        Config.WSPATH = f"wss://{Config.HOST}:{Config.port}"
    else:
        Config.WSPATH = f"ws://{Config.HOST}:{Config.port}"
    
    Config.PARAIVEW = args.paraview
    Config.PARAVIEW_PORT = args.paraview_port
    Config.PARAVIEW_DIR = args.paraview_dir
    Config.PARAVIEW_DATA_DIR = args.paraview_data_dir
    Config.PARAVIEW_SESSION_PORT_START = args.paraview_port_start
    
    if Config.PARAVIEW > 0:
        if Config.PARAVIEW == 1:
            launch_paraview(
                paraview_directory=Config.PARAVIEW_DIR, 
                hostname=Config.HOST,
                data_directory=args.paraview_data_dir,
                logs_directory=args.logs_dir,
                port=Config.PARAVIEW_PORT)
        if Config.PARAVIEW > 0:
            set_paraview_forwards()
        

    Config.THEIA=args.theia
    Config.THEIA_PORT = args.theia_port
    Config.THEIA_DIR = args.theia_dir
    
    if Config.THEIA > 0:
        if Config.THEIA == 1:
            launch_theia(
            theia_directory=Config.THEIA_DIR, 
            hostname=Config.HOST,
            logs_directory=args.logs_dir,
            port=Config.THEIA_PORT)
        if Config.THEIA > 0:    
            set_theia_forwards()
        
    
    Config.VNV=args.vnv
    Config.VNV_PORT=args.vnv_port
    Config.VNV_DIR = args.vnv_dir
    
    if Config.VNV > 0:
        launch_vnv_gui(
            vnv_directory=Config.VNV_DIR, 
            hostname=Config.HOST,
            logs_directory=args.logs_dir,
            port=Config.VNV_PORT)



    app_config = Config()   
    socketio, app = create_serve_app(app_config)
    
    opts = {
        "use_reloader" : False,
        "host" : app_config.HOST,
        "port" : app_config.port
    }
    
    if args.ssl:
        opts["ssl_context"] = (args.ssl_cert, args.ssl_key)

    socketio.run(app, **opts)

