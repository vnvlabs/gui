#!/bin/bash 

# Launch without mapping Theia and Paraview. This is used by the serve app
# Like serve.sh, this script starts the three servers on different ports. Unkike
# serve.sh, the Theia and paraview ports are not routed to the different ports. This
# configuration is designed to be used with an external proxy (as is used in the "serve" app).

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
                --theia=/theia \
                --paraview=/paraview




