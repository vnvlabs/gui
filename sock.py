# -*- encoding: utf-8 -*-
import argparse
import json
import os
import sys
import time

from flask import Flask
from flask_sock import Sock

from app import create_app

import sys


sock = Sock()

def create_app():
    app = Flask(__name__)
    sock.init_app(app)
    return app


import subprocess
wdir = "/home/ben/source/vnvlabs.com/vnvlabs/applications/moose/docker/moose-language-support/server"
command = ['node', 'out/server.js', '--stdio']
p = subprocess.Popen(command, cwd=wdir, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
os.set_blocking(p.stdout.fileno(), False)


@sock.route('/exampleServer')
def echo(ws):
    while True:

        data = ws.receive()
        p.stdin.write(data.encode() + b'\n')

        start = time.time()
        while True:
            # first iteration always produces empty byte string in non-blocking mode

            for i in range(2):
                line = p.stdout.readline()
                print(i, line)
                time.sleep(0.5)

            if time.time() > start + 5:
                break


if __name__ == "__main__":
    app = create_app()
    app.run(use_reloader=False, host="localhost", port=3000)
