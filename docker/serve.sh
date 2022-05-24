#!/bin/bash 

#Serve the app on the docker container.
# This creates three seperate servers and directly reroutes
# the paraview vis and theia ide to the correct ports. To use this,
# you need to make sure all the ports (5001,3000 and 9000) are exposed.

PARAVIEW_PORT=9000
THEIA_PORT=3000
GUI_PORT=5001
HOSTNAME=0.0.0.0


export PYTHONPATH=${VNV_DIR}

# Start mongo.sh
service mongodb start

# Start Theia in the source directory.
cd /theia
node /theia/src-gen/backend/main.js ${SOURCE_DIR} --port ${THEIA_PORT} --hostname=${HOSTNAME} &

# Start the paraview visualizer server
cd /paraview
$PVPYTHON -m paraview.apps.visualizer --host ${HOSTNAME} --data / --port ${PARAVIEW_PORT} --timeout 600000 &

cd /vnv-gui
virt/bin/python ./run.py \
                --host ${HOSTNAME} \
                --port ${GUI_PORT} \
                --theia http://${HOSTNAME}:${THEIA_PORT} \
                --paraview http://${HOSTNAME}:${PARAVIEW_PORT}




