#!/bin/bash 

# Launch with mapping Theia and Paraview. This is used by the serve app

HOST_PORT=5000
PARAVIEW_PORT=9000
THEIA_PORT=3000
GUI_PORT=5001
HOSTNAME=0.0.0.0
export PYTHONPATH=${VNV_DIR}

# Start mongo
#mkdir -p /data/db
#mongod &

mkdir /vnvgui/logs

# Start Theia in the source directory.
cd /vnvgui/theia
node /vnvgui/theia/browser-app/src-gen/backend/main.js / --port ${THEIA_PORT} --hostname=${HOSTNAME} --plugins=local-dir:/vnvgui/theia/browser-app/plugins &> /vnvgui/logs/theia_logs &

# Launch paraview, downloading it if DOWNLOAD_PARAVIEW is defined. 
cd /vnvgui/paraview
bin/pvpython -m paraview.apps.visualizer --host ${HOSTNAME} --data /home/user --port ${PARAVIEW_PORT} --timeout 600000 &> /vnvgui/logs/paraview_logs &

#Run the vnv gui
cd /vnvgui/gui
virt/bin/python ./run.py \
                --host ${HOSTNAME} \
                --port ${GUI_PORT} ${@:1} &> /vnvgui/logs/gui_logs &


echo "Now Running on port $HOST_PORT!"

# Launch the VnV Router on the Resource.
virt/bin/python router.py \
            --host ${HOSTNAME}\
	        --port ${HOST_PORT}\
	        --vnv ${GUI_PORT}  \
            --theia ${THEIA_PORT} \
            --paraview ${PARAVIEW_PORT} ${@:1} &> /vnvgui/router_logs


