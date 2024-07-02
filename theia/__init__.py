import os
import subprocess


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
            f'--plugins=local-dir:{theia_directory}/browser-app/plugins'
        ]

        log_file = f'{logs_directory}/theia_logs'
        with open(log_file, 'w') as log:
            child_processes = subprocess.Popen(command, stdout=log, stderr=log)

        os.chdir(curr_dir)
        return child_processes

    else:
        return None

def set_theia_forwards(theia_dir):
    forwards = []
    theiaforwards = subprocess.run(["ls", os.path.join(theia_dir, "browser-app/lib/frontend")],
                                   stdout=subprocess.PIPE).stdout.decode(
        'ascii').split("\n")
    for line in theiaforwards:
        kk = line.replace("\t", " ")
        forwards = forwards + kk.split(" ")
    return [a.strip() for a in forwards if len(a) > 0 and a != "index.html"] + ["os"]

