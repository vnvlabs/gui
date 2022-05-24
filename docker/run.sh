#!/bin/bash 

#Serve the app on the docker container.
# Completly handle all servers and routing. This creates a flask proxy in front of the
# three servers that handles forwarding. This is the ready to go solution.
# This runs on a single port (5001) so make sure that port is exposed.

cd /vnv-gui
virt/bin/python3 ./proxy.py


