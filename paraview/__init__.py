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
            if paraview_sessions[i].poll() is not None:
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

            if paraview_sessions[port].poll() is not None:
                PARAVIEW_FILE_SERVERS.pop(filename)
                paraview_sessions.pop(port)
                print("Closed it Tou:")
            else:
                return port, True


    with mutex_lock:
        port = pick_paraview_port(filename)


    if port is None:
        return port, False

    print("Launching Paraview on Port ", port, filename)
    cmd = [
        "bin/pvpython", "-m", "paraview.apps.visualizer", "--host", current_app.config["HOST"], "--port", str(port), "--data",
        current_app.config["PARAVIEW_DATA_DIR"], "--timeout", str(600000)
    ]

    if filename is not None and os.path.exists(filename):
        f = os.path.abspath(filename)
        cmd += ["--load-file", f[1:]]

    paraview_sessions[port] = subprocess.Popen(cmd, cwd=current_app.config["PARAVIEW_DIR"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, preexec_fn=preexec_function)

    PARAVIEW_FILE_SERVERS[filename] = port

    return port,True

def wait_for_paraview_to_start(port):

    start_time = time.time()

    while paraview_sessions[port].returncode is None:
        # Your loop code here
        current_time = time.time()
        elapsed_time = current_time - start_time
        if elapsed_time > 10:
            return port, False

        line = paraview_sessions[port].stdout.readline()
        if "Starting factory" in line.decode("ascii"):
            return port, True
        else:
            print(line)
            pass

    return port, False
