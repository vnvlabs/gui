#!/bin/bash 

# Launch with mapping Theia and Paraview. This is used by the serve app
DIRECT=$PWD
HOST_PORT=5000
PARAVIEW_PORT=9000
THEIA_PORT=3000
GUI_PORT=5001
HOSTNAME=0.0.0.0
export PYTHONPATH=${VNV_DIR}

# Start mongo
#mkdir -p /data/db
#mongod &

cleanup() {
    echo "Caught Ctrl+C. Cleaning up..."
    
    # Terminate background jobs
    for job in $(jobs -p); do
        kill "$job"
    done
    
    exit 1
}

# Set trap to catch Ctrl+C and call the cleanup function
trap cleanup SIGINT


mkdir /vnvgui/logs

# Start Theia in the source directory.
cd /vnvgui/theia
node /vnvgui/theia/browser-app/src-gen/backend/main.js / --port ${THEIA_PORT} --hostname=${HOSTNAME} --plugins=local-dir:/vnvgui/theia/browser-app/plugins &> /vnvgui/logs/theia_logs &
echo "Theia PID is $!"

# Launch paraview, downloading it if DOWNLOAD_PARAVIEW is defined. 
cd /vnvgui/paraview
bin/pvpython -m paraview.apps.visualizer --host ${HOSTNAME} --data /home/user --port ${PARAVIEW_PORT} --timeout 600000 &> /vnvgui/logs/paraview_logs &
echo "Parview PID is $!"

#Run the vnv gui
cd $DIRECT
virt/bin/python ./run.py \
                --host ${HOSTNAME} \
                --port ${GUI_PORT} ${@:1} &> /vnvgui/logs/gui_logs &
echo "GUI PI is $!"


echo "Router is running on port $HOST_PORT!"

# Launch the VnV Router on the Resource.
virt/bin/python router.py \
            --host ${HOSTNAME}\
	        --port ${HOST_PORT}\
	        --vnv ${GUI_PORT}  \
            --theia ${THEIA_PORT} \
            --paraview ${PARAVIEW_PORT} ${@:1} &> /vnvgui/logs/router_logs 





