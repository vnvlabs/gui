#!/bin/bash 

# Launch with mapping Theia and Paraview. This is used by the serve app

HOST_PORT=5000
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

# Start the VnV Server
cd /vnv-gui
virt/bin/python ./run.py \
                --host ${HOSTNAME} \
                --port ${GUI_PORT} \
                --theia=/theia \
                --paraview=/paraview &


# Launch the VnV Router on the Resource.
virt/bin/python router/run.py \
                --host ${HOSTNAME}\
	              --port ${HOST_PORT}\
	              --vnv ${GUI_PORT}  \
                --theia ${THEIA_PORT} \
                --paraview ${PARAVIEW_PORT} ${@:1}

