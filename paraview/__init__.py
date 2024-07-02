import os
import subprocess
import tarfile
import urllib.request

# URL of the file to be downloaded
url = "https://www.paraview.org/paraview-downloads/download.php?submit=Download&version=v5.10&type=binary&os=Linux&downloadFile=ParaView-5.10.1-osmesa-MPI-Linux-Python3.9-x86_64.tar.gz"
# Path where the file will be saved
tar_path = "pv.tar.gz"
# Directory where the tar file will be extracted
extract_dir = "<dir>"  # Replace <dir> with the actual directory

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
            child_processes = subprocess.Popen(command, stdout=log, stderr=log)

        os.chdir(curr_dir)
        return child_processes
    else:
        return None


def set_paraview_forwards(paraview_dir):
    forwards = []
    pvforwards = subprocess.run(["ls", os.path.join(paraview_dir, "share/paraview-5.10/web/visualizer/www")],
                                stdout=subprocess.PIPE).stdout.decode('ascii').split("\n")

    for line in pvforwards:
        kk = line.replace("\t", " ")
        forwards = forwards + kk.split(" ")

    return [a.strip() for a in forwards if len(a) > 0 and a != "index.html"]

