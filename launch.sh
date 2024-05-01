#!/bin/bash 

# Launch with mapping Theia and Paraview. This is used by the serve app
ROOTDIR=""

HOSTNAME=0.0.0.0
HOST_PORT=5000
LOGS_DIRECTORY="/home/ben/vnvgui/logs/"

VNV=1
VNV_PORT=5001
VNV_DIR="${ROOTDIR}/vnvgui/gui"

THEIA=1
THEIA_PORT=5002
THEIA_DIR="${ROOTDIR}/vnvgui/theia"

PARAVIEW=1
PARAVIEW_PORT=5003
PARAVIEW_DIR="${ROOT_DIR}/vnvgui/paraview"
PARAVIEW_PORT_START=5004
PARAVIEW_DATA_DIR="${ROOTDIR}/"

mkdir -p ${LOGS_DIRECTORY}

# Launch the VnV Router on the Resource.
virt/bin/python router.py \
            --host ${HOSTNAME}\
	        --port ${HOST_PORT}\
            --logs_dir ${LOGS_DIRECTORY} \
	        --vnv ${VNV} --vnv_dir ${VNV_DIR} --vnv_port ${VNV_PORT}  \
            --theia ${THEIA} --theia_dir ${THEIA_DIR} --theia_port ${THEIA_PORT} \
            --paraview ${PARAVIEW} --paraview_dir ${PARAVIEW_DIR} \
            --paraview_port ${PARAVIEW_PORT} --paraview_port_start ${PARAVIEW_PORT_START} \
            --paraview_data_dir ${PARAVIEW_DATA_DIR} \
            ${@:1} :
