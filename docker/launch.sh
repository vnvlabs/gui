#!/bin/bash 

# Launch with mapping Theia and Paraview. This is used by the serve app

HOST_PORT=5000
PARAVIEW_PORT=9000
THEIA_PORT=3000
GUI_PORT=5001
GLVIS_PORT=5007
HOSTNAME=0.0.0.0
export PYTHONPATH=${VNV_DIR}

# Start mongo
#mkdir -p /data/db
#mongod &

# Start Theia in the source directory.
cd /vnvgui/theia
node /vnvgui/theia/src-gen/backend/main.js / --port ${THEIA_PORT} --hostname=${HOSTNAME} --plugins=local-dir:/vnvgui/theia/plugins &

# Launch paraview, downloading it if DOWNLOAD_PARAVIEW is defined. 
cd /vnvgui/paraview
bin/pvpython -m paraview.apps.visualizer --host ${HOSTNAME} --data / --port ${PARAVIEW_PORT} --timeout 600000 &

# Start the GLVIS SERVER
cd /vnvgui/gui
virt/bin/python glvis/glvis.py --ws-port ${GLVIS_PORT} &

#Run the vnv gui
cd /vnvgui/gui
virt/bin/python ./run.py \
                --host ${HOSTNAME} \
                --port ${GUI_PORT} ${@:1} &

                # VnVLabs--theia https://vnvlabs.com/?theia

# Launch the VnV Router on the Resource.
virt/bin/python router.py \
            --host ${HOSTNAME}\
	        --port ${HOST_PORT}\
	        --vnv ${GUI_PORT}  \
            --theia ${THEIA_PORT} \
            --paraview ${PARAVIEW_PORT} ${@:1}
###For VnVLabs.com use this option --wspath wss://vnvlabs.com/ws


