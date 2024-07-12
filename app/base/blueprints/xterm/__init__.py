#!/usr/bin/env python3
import argparse
from flask import Flask, render_template, Blueprint, request
from flask_socketio import SocketIO
import pty
import os
import subprocess
import select
import termios
import struct
import fcntl
import shlex
import logging
import sys

from app.models.VnVFile import VnVFile
from app.models.VnVInputFile import VnVInputFile

blueprint = Blueprint(
    'xterm',
    __name__,
    template_folder='templates',
    url_prefix="/xterm"
)

socketio = SocketIO(path='/gui_socket.io')

CONNECTIONS = {}


def set_winsize(fd, row, col, xpix=0, ypix=0):
    winsize = struct.pack("HHHH", row, col, xpix, ypix)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)


def read_and_forward_pty_output(fd, id_):
    max_read_bytes = 1024 * 20
    while True:
        socketio.sleep(0.01)
        if fd:
            timeout_sec = 0
            (data_ready, _, _) = select.select([fd], [], [], timeout_sec)
            if data_ready:
                output = os.read(fd, max_read_bytes).decode(
                    errors="ignore"
                )
                socketio.emit("pty-output", {"output": output}, namespace="/pty")


def process(file, dir='/'):

    if file.getXtermId() in CONNECTIONS and CONNECTIONS[file.getXtermId()].get("cd"):
        pass
    else:

        # create child process attached to a pty we can read from and write to
        (cd, fd) = pty.fork()
        if cd == 0:
            subprocess.run("bash", cwd=dir)
        else:
            # this is the parent process fork.
            # store child fd and pid
            CONNECTIONS[file.getXtermId()] = {"fd": fd, "cd": cd, "o": []}
            set_winsize(fd, 50, 50)
            socketio.start_background_task(target=read_and_forward_pty_output, fd=fd, id_=file.getXtermId())

    return render_template("xterm/index.html", id_=file.getXtermId())

@blueprint.route("/ifile/<int:id_>")
def index(id_):

    with VnVInputFile.find(id_) as file:
        if os.path.exists(file.get_working_directory()):
            return process(file, dir=file.get_working_directory())
        else:
            return process(file, dir='/')


@blueprint.route("/file/<int:id_>")
def index1(id_):

    with VnVFile.find(id_) as file:
        if os.path.exists(file.get_working_directory()):
            return process(file, dir=file.get_working_directory())
        else:
            return process(file, dir='/')


@socketio.on("pty-input", namespace="/pty")
def pty_input(data):
    """write to the child pty. The pty sees this as if you are typing in a real
    terminal.
    """
    fd = CONNECTIONS.get(data["id"],{}).get("fd")
    if fd:
        os.write(fd, data["input"].encode())


@socketio.on("resize", namespace="/pty")
def resize(data):
    fd = CONNECTIONS.get(data["id"],{}).get("fd")
    if fd:
        set_winsize(fd, data["rows"], data["cols"])

@socketio.on("connect", namespace="/pty")
def connect():
    pass

def setup_app(app):
    socketio.init_app(app)

