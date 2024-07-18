import os
import signal
import subprocess

def preexec_function():
    import ctypes
    libc = ctypes.CDLL('libc.so.6')
    libc.prctl(1, signal.SIGTERM)

def launch_theia(theia_directory, logs_directory, hostname, port, node="node", home="/"):
    if os.path.exists(f"{theia_directory}/browser-app/src-gen/backend/main.js"):

        curr_dir = os.getcwd()
        os.chdir(theia_directory)

        command = [
            node,
            './browser-app/src-gen/backend/main.js',
            '/',
            '--port', str(port),
            '--hostname=' + hostname,
            f'--plugins=local-dir:{theia_directory}/browser-app/plugins',
            home
        ]

        log_file = f'{logs_directory}/theia_logs'
        with open(log_file, 'w') as log:
            child_processes = subprocess.Popen(command, stdout=log, stderr=log, preexec_fn=preexec_function)

        os.chdir(curr_dir)
        return child_processes

    else:
        return None

