import os
import signal
import subprocess
import tarfile
import time
import urllib.request
from threading import Lock

from flask import current_app

# URL of the file to be downloaded
url = "https://www.paraview.org/paraview-downloads/download.php?submit=Download&version=v5.10&type=binary&os=Linux&downloadFile=ParaView-5.10.1-osmesa-MPI-Linux-Python3.9-x86_64.tar.gz"
# Path where the file will be saved
tar_path = "pv.tar.gz"
# Directory where the tar file will be extracted
extract_dir = "<dir>"  # Replace <dir> with the actual directory

paraview_sessions = {}

class ParaviewSession:
    def __init__(self, port, cmd):

        #self.process = subprocess.Popen(cmd, env={"PYTHONUNBUFFERED":"1"}, cwd=current_app.config["PARAVIEW_DIR"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.process = os.system(' '.join(cmd) + " &")
        self.started = False
        self.launchTime = time.time()
        self.port = port
        self.isstarted = False

    def isdone(self):
        False
        #return  self.process.poll() is not None


    def wait_till_launched(self):

        while not self.isdone():
          if self.isstarted:
              return self.port, True
          time.sleep(5)
          self.isstarted = True
          return self.port, True


# Function to download the file
def download_file(url, path):
    print(f"Downloading {url}...")
    urllib.request.urlretrieve(url, path)
    print(f"Downloaded to {path}")

# Function to extract the tar file
def extract_tar_file(tar_path, extract_dir):
    print(f"Extracting {tar_path} to {extract_dir}...")
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=extract_dir)
    print(f"Extracted to {extract_dir}")

# Function to delete the tar file
def delete_file(path):
    print(f"Deleting {path}...")
    os.remove(path)
    print(f"Deleted {path}")

def download_paraview(paraview_dir):
    download_file(url, tar_path)
    extract_tar_file(tar_path, paraview_dir)
    delete_file(tar_path)


PARAVIEW_FILE_SERVERS = {}

PARAVIEW_MAX = 20



def preexec_function():
    import ctypes
    libc = ctypes.CDLL('libc.so.6')
    libc.prctl(1, signal.SIGTERM)

def pick_paraview_port(filename):

    port = None
    for i in range(current_app.config["PARAVIEW_SESSION_PORT_START"], current_app.config["PARAVIEW_SESSION_PORT_END"]):

        # Check if in use
        if i in paraview_sessions:

            # If was used but now closed, then delete it.
            if paraview_sessions[i].isdone() is not None:
                paraview_sessions.pop(i)
                port = i
                break
            else:
                pass
        else:
            port = i
            break

    return port

mutex_lock = Lock()

def start_paraview_server(filename):

    if filename is None:
        if filename in PARAVIEW_FILE_SERVERS:
            port = PARAVIEW_FILE_SERVERS[filename]

            if paraview_sessions[port].isdone():
                PARAVIEW_FILE_SERVERS.pop(filename)
                paraview_sessions.pop(port)
                print("Closed it Out:")
            else:
                return port, True


    with mutex_lock:
        port = pick_paraview_port(filename)
        if port is None:
            return port, False

        print("Launching Paraview on Port ", port, filename)
        cmd = [
            "{current_app.config['PARAVIEW_DIR']}bin/pvpython", "-u", "-m", "paraview.apps.visualizer", "--host", "0.0.0.0", "--port", str(port), "--data", '/', "--timeout", "660000"
        ]



        if filename is not None and os.path.exists(filename):
            f = os.path.abspath(filename)
            cmd += ["--load-file", f[1:]]

        paraview_sessions[port] = ParaviewSession(port, cmd)

        PARAVIEW_FILE_SERVERS[filename] = port

    return port,True



def wait_for_paraview_to_start(port):

    start_time = time.time()

    if port not in paraview_sessions:
        return port, False

    return paraview_sessions[port].wait_till_launched()
